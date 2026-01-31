"""
Uber Shopping Ranking - Synthetic Product Data Generator

Generates 2000 realistic e-commerce products for ranking experiments.
Focus: Shopping intent signals (price sensitivity, popularity, category match)
"""

import json
import random
import hashlib
import os
from pathlib import Path

# Shopping-focused categories with realistic subcategories
CATEGORIES = {
    "Electronics": {
        "subcategories": ["Headphones", "Smartphones", "Laptops", "Tablets", "Cameras", "Smartwatches", "Speakers", "Gaming"],
        "brands": ["Sony", "Samsung", "Apple", "Bose", "JBL", "LG", "Anker", "Logitech"],
        "price_range": (29.99, 1999.99),
        "keywords": ["wireless", "bluetooth", "HD", "pro", "ultra", "premium", "smart", "portable"]
    },
    "Clothing": {
        "subcategories": ["T-Shirts", "Jeans", "Dresses", "Jackets", "Shoes", "Activewear", "Accessories"],
        "brands": ["Nike", "Adidas", "Levi's", "Zara", "H&M", "Under Armour", "Puma", "Gap"],
        "price_range": (14.99, 299.99),
        "keywords": ["cotton", "slim fit", "casual", "athletic", "comfortable", "stylish", "breathable"]
    },
    "Home & Kitchen": {
        "subcategories": ["Cookware", "Appliances", "Bedding", "Storage", "Decor", "Cleaning", "Furniture"],
        "brands": ["KitchenAid", "Instant Pot", "Dyson", "Ninja", "OXO", "Cuisinart", "Rubbermaid"],
        "price_range": (9.99, 599.99),
        "keywords": ["stainless steel", "non-stick", "compact", "efficient", "modern", "durable"]
    },
    "Sports & Outdoors": {
        "subcategories": ["Fitness", "Camping", "Cycling", "Running", "Yoga", "Team Sports", "Swimming"],
        "brands": ["Nike", "Adidas", "The North Face", "Columbia", "Fitbit", "Garmin", "Yeti"],
        "price_range": (12.99, 499.99),
        "keywords": ["lightweight", "waterproof", "durable", "professional", "performance", "outdoor"]
    },
    "Beauty & Personal Care": {
        "subcategories": ["Skincare", "Haircare", "Makeup", "Fragrances", "Bath & Body", "Men's Grooming"],
        "brands": ["L'Oreal", "Nivea", "Dove", "Neutrogena", "Olay", "Maybelline", "Gillette"],
        "price_range": (4.99, 149.99),
        "keywords": ["organic", "natural", "hydrating", "anti-aging", "gentle", "long-lasting"]
    },
    "Books & Media": {
        "subcategories": ["Fiction", "Non-Fiction", "Self-Help", "Textbooks", "Comics", "Audiobooks"],
        "brands": ["Penguin", "HarperCollins", "Random House", "Simon & Schuster", "Scholastic"],
        "price_range": (7.99, 79.99),
        "keywords": ["bestseller", "award-winning", "classic", "new release", "illustrated"]
    },
    "Toys & Games": {
        "subcategories": ["Action Figures", "Board Games", "Puzzles", "Building Sets", "Dolls", "Outdoor Toys"],
        "brands": ["LEGO", "Hasbro", "Mattel", "Fisher-Price", "Nintendo", "Nerf", "Hot Wheels"],
        "price_range": (9.99, 299.99),
        "keywords": ["educational", "interactive", "collectible", "classic", "creative", "fun"]
    }
}

# Shopping intent templates - what real shoppers search for
TITLE_TEMPLATES = {
    "Electronics": [
        "{brand} {keyword} {subcategory}",
        "{keyword} {subcategory} with {feature}",
        "{brand} {subcategory} - {keyword} Edition",
        "Premium {keyword} {subcategory} by {brand}"
    ],
    "Clothing": [
        "{brand} {keyword} {subcategory}",
        "Men's/Women's {keyword} {subcategory}",
        "{brand} {subcategory} - {keyword} Style",
        "{keyword} {subcategory} for Everyday Wear"
    ],
    "Home & Kitchen": [
        "{brand} {keyword} {subcategory}",
        "{subcategory} Set - {keyword} Design",
        "{brand} {subcategory} with {feature}",
        "Professional {keyword} {subcategory}"
    ],
    "Sports & Outdoors": [
        "{brand} {keyword} {subcategory} Gear",
        "{subcategory} Equipment - {keyword}",
        "{brand} Pro {subcategory}",
        "{keyword} {subcategory} for Athletes"
    ],
    "Beauty & Personal Care": [
        "{brand} {keyword} {subcategory}",
        "{subcategory} - {keyword} Formula",
        "{brand} {keyword} {subcategory} Collection",
        "Daily {keyword} {subcategory}"
    ],
    "Books & Media": [
        "{keyword} {subcategory}: A Journey",
        "The Complete Guide to {subcategory}",
        "{keyword} Stories: {subcategory} Edition",
        "Mastering {subcategory}"
    ],
    "Toys & Games": [
        "{brand} {keyword} {subcategory}",
        "{subcategory} Set - {keyword} Edition",
        "{brand} {subcategory} Collection",
        "{keyword} {subcategory} for All Ages"
    ]
}

FEATURES = [
    "Fast Charging", "Voice Control", "LED Display", "Touch Screen",
    "Noise Cancellation", "Water Resistant", "Eco-Friendly", "Compact Design",
    "Long Battery Life", "Quick Setup", "Smart Features", "Premium Materials"
]


def generate_product_id(index: int) -> str:
    """Generate unique product ID."""
    return f"P{index:04d}"


def generate_description(category: str, subcategory: str, brand: str, keywords: list) -> str:
    """Generate realistic product description focused on shopping intent."""
    keyword = random.choice(keywords)
    
    templates = [
        f"Experience the best in {subcategory.lower()} with this {keyword} product from {brand}. "
        f"Designed for everyday use with premium quality materials.",
        
        f"This {keyword} {subcategory.lower()} from {brand} delivers exceptional performance. "
        f"Perfect for those who value quality and reliability.",
        
        f"Introducing the {brand} {subcategory.lower()} - featuring {keyword} technology. "
        f"Ideal for home and professional use.",
        
        f"Upgrade your {category.lower()} collection with this {keyword} {subcategory.lower()}. "
        f"{brand} brings you innovation and style combined.",
        
        f"The perfect {subcategory.lower()} for your needs. {brand}'s {keyword} design ensures "
        f"top performance and durability."
    ]
    
    return random.choice(templates)


def generate_popularity_score(rating: float, price: float, category: str) -> float:
    """
    Generate popularity score based on shopping signals:
    - Higher rated products are more popular
    - Mid-range prices often have higher popularity (value perception)
    - Some categories are inherently more popular
    """
    base_score = (rating - 3.0) / 2.0  # Rating contribution: -1 to 1
    
    # Price sweet spot (mid-range is often most popular)
    cat_range = CATEGORIES[category]["price_range"]
    mid_price = (cat_range[0] + cat_range[1]) / 2
    price_factor = 1 - abs(price - mid_price) / (cat_range[1] - cat_range[0])
    
    # Category popularity weights (electronics and clothing tend to be searched more)
    category_weights = {
        "Electronics": 1.2,
        "Clothing": 1.1,
        "Home & Kitchen": 1.0,
        "Sports & Outdoors": 0.95,
        "Beauty & Personal Care": 1.0,
        "Books & Media": 0.85,
        "Toys & Games": 0.9
    }
    
    # Combine factors
    raw_score = (0.4 * base_score + 0.3 * price_factor + 0.3 * random.random()) * category_weights[category]
    
    # Normalize to 0-1
    return round(max(0.1, min(0.99, (raw_score + 1) / 2)), 3)


def generate_products(num_products: int = 2000) -> list:
    """Generate synthetic product catalog."""
    products = []
    
    for i in range(1, num_products + 1):
        # Pick category and details
        category = random.choice(list(CATEGORIES.keys()))
        cat_info = CATEGORIES[category]
        
        subcategory = random.choice(cat_info["subcategories"])
        brand = random.choice(cat_info["brands"])
        keyword = random.choice(cat_info["keywords"])
        feature = random.choice(FEATURES)
        
        # Generate title using templates
        template = random.choice(TITLE_TEMPLATES[category])
        title = template.format(
            brand=brand,
            keyword=keyword.title(),
            subcategory=subcategory,
            feature=feature
        )
        
        # Generate other fields
        price = round(random.uniform(*cat_info["price_range"]), 2)
        rating = round(random.uniform(3.0, 5.0), 1)
        
        # Shopping-focused fields
        product = {
            "product_id": generate_product_id(i),
            "title": title,
            "description": generate_description(category, subcategory, brand, cat_info["keywords"]),
            "category": category,
            "subcategory": subcategory,
            "price": price,
            "brand": brand,
            "rating": rating,
            "popularity_score": generate_popularity_score(rating, price, category),
            "in_stock": random.random() > 0.1,  # 90% in stock
            "review_count": random.randint(5, 2000),
            "image_url": f"https://picsum.photos/seed/{generate_product_id(i)}/400/400"
        }
        
        products.append(product)
        
        if i % 500 == 0:
            print(f"Generated {i}/{num_products} products...")
    
    return products


def main():
    """Main execution."""
    print("🛒 Uber Shopping Ranking - Data Generator")
    print("=" * 50)
    
    # Create data directory
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Generate products
    num_products = int(os.environ.get("NUM_PRODUCTS", 500))
    print(f"\n📦 Generating {num_products} synthetic products...")
    products = generate_products(num_products)
    
    # Save to JSON
    output_path = data_dir / "products_clean.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved {len(products)} products to {output_path}")
    
    # Print statistics
    print("\n📊 Category Distribution:")
    category_counts = {}
    for p in products:
        category_counts[p["category"]] = category_counts.get(p["category"], 0) + 1
    
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"   {cat}: {count} products")
    
    print("\n💰 Price Statistics:")
    prices = [p["price"] for p in products]
    print(f"   Min: ${min(prices):.2f}")
    print(f"   Max: ${max(prices):.2f}")
    print(f"   Avg: ${sum(prices)/len(prices):.2f}")
    
    print("\n⭐ Rating Statistics:")
    ratings = [p["rating"] for p in products]
    print(f"   Min: {min(ratings)}")
    print(f"   Max: {max(ratings)}")
    print(f"   Avg: {sum(ratings)/len(ratings):.2f}")


if __name__ == "__main__":
    main()
