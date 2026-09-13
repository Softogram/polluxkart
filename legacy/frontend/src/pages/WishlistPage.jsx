import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Heart, ShoppingCart, Trash2, ArrowRight } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '../components/ui/breadcrumb';
import { useWishlist } from '../context/WishlistContext';
import { useCart } from '../context/CartContext';
import { formatPrice } from '../utils/currency';
import { toast } from 'sonner';

const WishlistPage = () => {
  const navigate = useNavigate();
  const { wishlistItems, removeFromWishlist, clearWishlist } = useWishlist();
  const { addToCart } = useCart();

  const handleAddToCart = (product) => {
    if (!product.inStock) {
      toast.error('This item is currently out of stock');
      return;
    }
    addToCart(product, 1);
    toast.success(`${product.name} added to cart!`);
  };

  const handleMoveAllToCart = () => {
    const inStockItems = wishlistItems.filter(item => item.inStock !== false);
    if (inStockItems.length === 0) {
      toast.error('No items in stock to add to cart');
      return;
    }
    inStockItems.forEach(item => addToCart(item, 1));
    toast.success(`${inStockItems.length} items added to cart!`);
  };

  if (wishlistItems.length === 0) {
    return (
      <div className="min-h-screen bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Breadcrumb className="mb-6">
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink asChild>
                  <Link to="/">Home</Link>
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbPage>Wishlist</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>

          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-24 h-24 rounded-full bg-muted flex items-center justify-center mb-6">
              <Heart className="h-12 w-12 text-muted-foreground" />
            </div>
            <h2 className="font-heading text-2xl font-bold text-foreground mb-2">
              Your wishlist is empty
            </h2>
            <p className="text-muted-foreground mb-6">
              Save items you love by clicking the heart icon on products.
            </p>
            <Button onClick={() => navigate('/store')}>
              Start Shopping
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Breadcrumb */}
        <Breadcrumb className="mb-6">
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink asChild>
                <Link to="/">Home</Link>
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage>Wishlist</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>

        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="font-heading text-3xl font-bold text-foreground">My Wishlist</h1>
            <p className="text-muted-foreground mt-1">
              {wishlistItems.length} {wishlistItems.length === 1 ? 'item' : 'items'} saved
            </p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={handleMoveAllToCart}>
              <ShoppingCart className="mr-2 h-4 w-4" />
              Add All to Cart
            </Button>
            <Button
              variant="ghost"
              className="text-destructive hover:text-destructive hover:bg-destructive/10"
              onClick={() => {
                clearWishlist();
                toast.success('Wishlist cleared');
              }}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Clear All
            </Button>
          </div>
        </div>

        {/* Wishlist Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {wishlistItems.map((product) => {
            const isOutOfStock = product.inStock === false;
            
            return (
              <Card 
                key={product.id} 
                className={`overflow-hidden transition-all ${
                  isOutOfStock 
                    ? 'opacity-60 bg-muted/50' 
                    : 'hover:shadow-lg'
                }`}
              >
                {/* Image */}
                <Link to={`/product/${product.id}`}>
                  <div className="relative aspect-square overflow-hidden bg-muted/30">
                    <img
                      src={product.image}
                      alt={product.name}
                      className={`w-full h-full object-cover transition-transform ${
                        isOutOfStock ? 'grayscale' : 'hover:scale-105'
                      }`}
                    />
                    {isOutOfStock && (
                      <div className="absolute inset-0 bg-background/60 flex items-center justify-center">
                        <Badge variant="secondary" className="bg-destructive/90 text-destructive-foreground text-sm">
                          Out of Stock
                        </Badge>
                      </div>
                    )}
                    {product.badge && !isOutOfStock && (
                      <Badge className="absolute top-3 left-3 bg-primary text-primary-foreground">
                        {product.badge}
                      </Badge>
                    )}
                  </div>
                </Link>

                {/* Content */}
                <CardContent className="p-4">
                  <Link to={`/product/${product.id}`}>
                    <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
                      {product.category}
                    </p>
                    <h3 className="font-medium text-sm line-clamp-2 text-foreground hover:text-primary transition-colors mb-2">
                      {product.name}
                    </h3>
                  </Link>

                  {/* Price */}
                  <div className="flex items-center gap-2 mb-4">
                    <span className="font-heading font-bold text-lg text-foreground">
                      {formatPrice(product.price)}
                    </span>
                    {product.originalPrice && (
                      <span className="text-sm text-muted-foreground line-through">
                        {formatPrice(product.originalPrice)}
                      </span>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <Button
                      className="flex-1"
                      onClick={() => handleAddToCart(product)}
                      disabled={isOutOfStock}
                    >
                      <ShoppingCart className="mr-2 h-4 w-4" />
                      {isOutOfStock ? 'Out of Stock' : 'Add to Cart'}
                    </Button>
                    <Button
                      variant="outline"
                      size="icon"
                      className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                      onClick={() => {
                        removeFromWishlist(product.id);
                        toast.success('Removed from wishlist');
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default WishlistPage;
