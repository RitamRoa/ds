# -*- coding: utf-8 -*-
from app import app, db, MenuItem

def init_menu_items():
    menu_items = [
        MenuItem(
            name="Mushroom Swiss Burger",
            price=799.00,
            stock=50,
            description="Juicy beef patty with sauteed mushrooms and Swiss cheese"
        ),
        MenuItem(
            name="Margherita Pizza",
            price=1499.00,
            stock=50,
            description="Classic pizza with tomato sauce, mozzarella, and basil"
        ),
        MenuItem(
            name="Pasta Carbonara",
            price=1099.00,
            stock=50,
            description="Creamy pasta with bacon, egg, and parmesan"
        ),
        MenuItem(
            name="Poke Bowl",
            price=899.00,
            stock=50,
            description="Fresh tuna with rice, vegetables, and special sauce"
        ),
        MenuItem(
            name="Loaded Nachos",
            price=999.00,
            stock=50,
            description="Crispy nachos topped with cheese, jalapenos, and salsa"
        ),
        MenuItem(
            name="Grilled Cheese Sandwich",
            price=1299.00,
            stock=50,
            description="Classic grilled cheese with premium cheddar"
        )
    ]
    
    with app.app_context():
        # Clear existing menu items
        MenuItem.query.delete()
        
        # Add new menu items
        for item in menu_items:
            db.session.add(item)
        
        db.session.commit()
        print("Menu items initialized successfully!")

if __name__ == "__main__":
    init_menu_items() 