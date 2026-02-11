from app.models.product import Product as ProductModel


def prepare_product_text(product: ProductModel) -> dict:
    category_names = []
    if product.categories:
        category_names = [cat.name for cat in product.categories]

    text = f"Description: {product.description}, \n Categories: {category_names}, \n Price: {product.price}"
    return {"text": text, "title": product.name}
