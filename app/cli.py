import sys
import json
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import typer
from app.db.session import SessionLocal
from app.services.user import user_service
from app.schemas.user import UserCreate
from app.services.product import product_service
from app.services.category import category_service
from app.schemas.product import ProductCreate
from app.schemas.category import CategoryCreate
from app.models.product import Product
from app.utils.product_text import prepare_product_text
from app.services.embedding import GeminiEmbeddingService
from app.services.vector_store import MilvusVectorStore
from app.core.config import settings

cli = typer.Typer()


@cli.command()
def create_superuser(
    email: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True),
    full_name: str = typer.Option(..., prompt=True),
):
    """Create a superuser."""
    db = SessionLocal()
    try:
        user = user_service.create(
            db,
            obj_in=UserCreate(
                email=email, password=password, full_name=full_name, is_superuser=True
            ),
        )
        typer.echo(f"Superuser created successfully! UUID: {user.uuid}")
    finally:
        db.close()


@cli.command()
def populate_dummy_data():
    """Populate database with dummy products and categories from local data.json."""
    db = SessionLocal()
    try:
        # Clean up existing data
        typer.echo("Cleaning up existing data...")
        # Delete products and categories; association entries will be removed via cascade
        db.query(product_service.model).delete()
        db.query(category_service.model).delete()
        db.commit()
        typer.echo("Existing products and categories deleted.")

        # Load local product data from app/data.json
        data_path = Path(__file__).resolve().parent / "data.json"
        if not data_path.exists():
            typer.echo(f"data.json not found at {data_path}", err=True)
            raise typer.Exit(1)

        with data_path.open() as f:
            products_data = json.load(f)

        # Create categories dynamically from data.json
        typer.echo("Creating categories...")
        category_mapping = {}  # normalized_name -> category UUID
        for item in products_data:
            raw_name = item.get("category", "").strip()
            if not raw_name:
                continue
            key = raw_name.lower()
            if key in category_mapping:
                continue

            category = category_service.create(
                db,
                obj_in=CategoryCreate(
                    name=raw_name,
                    description=f"{raw_name} products",
                ),
            )
            category_mapping[key] = category.uuid
            typer.echo(f"Created category: {raw_name}")

        # Create products
        typer.echo("\nCreating products from data.json...")
        used_names = set()
        total_products = 0

        for item in products_data:
            title = item.get("title")
            description = item.get("description") or ""
            price = float(item.get("price", 0))
            stock = int(item.get("stock", 0))
            category_name = item.get("category", "").strip()
            key = category_name.lower()

            if not title or not category_name or key not in category_mapping:
                continue

            if title in used_names:
                continue

            used_names.add(title)

            product_in = ProductCreate(
                name=title,
                price=price,
                description=description,
                images=[],  # No images in data.json
                category_uuids=[category_mapping[key]],
                stock_quantity=stock,
                size_guide="Standard sizing applies",
            )
            created_product = product_service.create(db, obj_in=product_in)
            typer.echo(f"Created product: {created_product.name}")
            total_products += 1

        typer.echo(
            f"\nDummy data population completed successfully! Created {total_products} products across {len(category_mapping)} categories."
        )

    except Exception as e:
        typer.echo(f"Error populating dummy data: {str(e)}", err=True)
        raise typer.Exit(1)
    finally:
        db.close()


@cli.command()
def generate_all_embeddings(
    max_workers: int = typer.Option(
        10,
        help="Maximum number of concurrent worker threads to use for embedding generation",
    )
):
    from concurrent.futures import ThreadPoolExecutor, as_completed

    db = SessionLocal()
    try:
        # Load product UUIDs up front to avoid sharing ORM instances across threads
        products = db.query(Product.uuid).all()
        total = len(products)
        if total == 0:
            typer.echo("No products found to generate embeddings for.")
            return

        typer.echo(
            f"Generating embeddings for {total} products using up to {max_workers} worker threads..."
        )

        # Initialize collection once (single-threaded) to ensure schema is correct
        embedding_service = GeminiEmbeddingService()
        vector_store = MilvusVectorStore()
        collection_name = settings.MILVUS_COLLECTION_NAME

        if not vector_store.collection_exists(collection_name):
            dimension = embedding_service.get_embedding_dimension()
            vector_store.initialize_collection(collection_name, dimension)
            typer.echo(
                f"Created Milvus collection '{collection_name}' with dim={dimension}"
            )

        # Release initial DB session; workers will open their own sessions
        db.close()

        def process_product(product_uuid):
            local_db = SessionLocal()
            try:
                product = (
                    local_db.query(Product).filter_by(uuid=product_uuid).one_or_none()
                )
                if not product:
                    return (product_uuid, False, "Product not found")

                local_embedding_service = GeminiEmbeddingService()
                local_vector_store = MilvusVectorStore()

                product_text = prepare_product_text(product)
                embedding = local_embedding_service.generate_embedding(product_text)

                local_vector_store.update_vector(
                    collection_name=collection_name,
                    vector_id=product.uuid,
                    vector=embedding,
                    metadata={"price": float(product.price)},
                )

                product.version += 1
                product.embedding_status = Product.EMBEDDING_STATUS_GENERATED
                local_db.commit()
                return (product_uuid, True, None)
            except Exception as e:
                local_db.rollback()
                if "product" in locals() and product is not None:
                    product.embedding_status = Product.EMBEDDING_STATUS_FAILED
                    local_db.commit()
                return (product_uuid, False, str(e))
            finally:
                local_db.close()

        processed = 0
        errors = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_product, row[0]) for row in products]

            for future in as_completed(futures):
                product_uuid, ok, err = future.result()
                processed += 1
                if ok:
                    typer.echo(
                        f"[OK] Processed {processed} of {total} products ({product_uuid})"
                    )
                else:
                    errors += 1
                    typer.echo(
                        f"[ERROR] Failed processing product {product_uuid}: {err}",
                        err=True,
                    )

        typer.echo(
            f"Embedding generation completed. Processed: {processed}, Errors: {errors}"
        )
    finally:
        try:
            db.close()
        except Exception:
            pass


@cli.command()
def test_semantic_search(
    query: str = typer.Option(..., prompt=True, help="Search query to test"),
    limit: int = typer.Option(10, help="Number of results to return"),
):
    """Test semantic search functionality."""
    from app.services.semantic_search import semantic_search_service

    db = SessionLocal()
    try:
        typer.echo(f"Searching for: '{query}'...")

        results, total = semantic_search_service.search(db=db, query=query, limit=limit)

        if not results:
            typer.echo(
                "No results found. Make sure embeddings have been generated for products."
            )
            return

        typer.echo(f"\nFound {total} results:\n")
        for i, result in enumerate(results, 1):
            product = result["product"]
            score = result["score"]
            typer.echo(f"{i}. {product.name}")
            typer.echo(f"   Description: {product.description}")
            typer.echo(f"   Price: {product.price}")
            typer.echo(
                f"   Categories: {', '.join([cat.name for cat in product.categories])}"
            )
            typer.echo(f"   Similarity Score: {score:.4f}")
            typer.echo(f"   UUID: {product.uuid}")
            typer.echo()

    except Exception as e:
        typer.echo(f"Error testing semantic search: {str(e)}", err=True)
        import traceback

        traceback.print_exc()
        raise typer.Exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    cli()
