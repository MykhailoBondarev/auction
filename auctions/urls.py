from django.urls import path
from django.conf.urls import handler404
from . import views

urlpatterns = [    
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("my-auctions", views.my_auctions, name="my-auctions"),
    path("new-auction", views.new_auction, name="new-auction"),
    path("lot/<int:lot_id>", views.lot_view, name="lot"),
    path("lot-activate", views.lot_activate, name="lot-activate"),
    path("category/<int:cat_id>", views.category_view, name="category"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("change-watchlist/<int:lot_id>", views.change_watchlist, name="change-watchlist"),
    path("add-rate", views.add_rate, name="add-rate"),
    path("add-comment", views.add_comment, name="add-comment"),
    path("profile", views.profile, name="profile"),
    path("search", views.search, name="search")
]

handler404 = 'auctions.views.not_found'