from django.urls import path, include

from api.views.admin.User import UserAdminList, UserAdminDetail
from api.views.admin.product import ProductClassAdminList, ProductClassAdminDetail, ProductAttributeAdminList, \
    ProductAttributeAdminDetail, ProductStockRecordsAdminList, ProductAdminList, ProductAdminDetail, \
    ProductStockRecordsAdminDetail, ProductCategoryList, ProductCategoryDetail
from api.views.basic import BasketList, BasketDetail
from api.views.basket import BasketView, AddProductView, LineList, LineDetail
from api.views.login import UserDetail, LoginView
from api.views.product import CategoryList, CategoryDetail, ProductStockRecords, ProductStockRecordDetail, ProductList, \
    ProductDetail
from api.views.root import api_root

urlpatterns = [
    path("", api_root, name="api-root"),
    path("login/", LoginView.as_view(), name="api-login"),
    path('basket', BasketView.as_view(), name='api-basket'),
    path('add_product', AddProductView.as_view(), name='add-product'),
    path('baskets', BasketList.as_view(), name='baskets-list'),
    path('baskets/<int:pk>', BasketDetail.as_view(), name='basket-detail'),
    path('baskets/<int:pk>/lines', LineList.as_view(), name='basket-lines-list'),
    path('baskets/<int:basket_pk>/lines/<int:pk>/', LineDetail.as_view(), name='basket-line-detail'),
    path("products/", ProductList.as_view(), name="product-list"),
    path("products/<int:pk>/", ProductDetail.as_view(), name="product-detail"),
    path(
        "products/<int:pk>/stockrecords/",
        ProductStockRecords.as_view(),
        name="product-stockrecords",
    ),
    path(
        "products/<int:product_pk>/stockrecords/<int:pk>/",
        ProductStockRecordDetail.as_view(),
        name="product-stockrecord-detail",
    ),
    path("categories/", CategoryList.as_view(), name="category-list"),
    path("categories/<int:pk>/", CategoryDetail.as_view(), name="category-detail"),
    path("users/<int:pk>/", UserDetail.as_view(), name="user-detail"),
]

admin_urlpatterns = [
    path('products/', ProductAdminList.as_view(), name='admin-product-list'),
    path('products/<int:pk>/', ProductAdminDetail.as_view(), name='admin-product-detail'),
    path('productclasses/', ProductClassAdminList.as_view(), name='admin-product-class-list'),
    path('productclasses/<int:pk>/', ProductClassAdminDetail.as_view(), name='admin-product-class-detail'),
    path('categories/', ProductCategoryList.as_view(), name='admin-categories-list'),
    path('categories/<int:pk>/', ProductCategoryDetail.as_view(), name='admin-categories-detail'),
    path('attributes', ProductAttributeAdminList.as_view(), name='admin-productattr-list'),
    path('attributes/<int:pk>/', ProductAttributeAdminDetail.as_view(), name='admin-productattr-detail'),
    path('stockrecords/', ProductStockRecordsAdminList.as_view(), name='admin-stockrecord-list'),
    path('stockrecords/<int:pk>/', ProductStockRecordsAdminDetail.as_view(), name='admin-stockrecord-detail'),
    path("users/", UserAdminList.as_view(), name="admin-user-list"),
    path("users/<int:pk>/", UserAdminDetail.as_view(), name="admin-user-detail"),
]

urlpatterns.append(path("admin/", include(admin_urlpatterns)))