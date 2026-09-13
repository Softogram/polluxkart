import React from 'react';
import { Link } from 'react-router-dom';
import { Star, ShoppingCart, Heart, Eye } from 'lucide-react';
import { Card, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { useCart } from '../../context/CartContext';
import { useWishlist } from '../../context/WishlistContext';
import { formatPrice } from '../../utils/currency';
import { toast } from 'sonner';

const ProductCard = ({ product }) => {
  const { addToCart } = useCart();
  const { isInWishlist, toggleWishlist } = useWishlist();
  
  const inWishlist = isInWishlist(product.id);
  const isOutOfStock = product.inStock === false;

  const handleAddToCart = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (isOutOfStock) {
      toast.error('This item is currently out of stock');
      return;
    }
    
    addToCart(product, 1);
    toast.success(`${product.name} added to cart!`);
  };

  const handleToggleWishlist = (e) => {
    e.preventDefault();
    e.stopPropagation();
    const added = toggleWishlist(product);
    if (added) {
      toast.success('Added to wishlist!');
    } else {
      toast.success('Removed from wishlist');
    }
  };

  const discount = product.originalPrice
    ? Math.round(((product.originalPrice - product.price) / product.originalPrice) * 100)
    : 0;

  return (
    <Link to={`/product/${product.id}`}>
      <Card className={`group relative overflow-hidden border border-border/50 bg-card transition-all duration-300 ${
        isOutOfStock 
          ? 'opacity-75 hover:opacity-90' 
          : 'hover:border-primary/30 hover:shadow-lg'
      }`}>
        {/* Image Container */}
        <div className="relative aspect-square overflow-hidden bg-muted/30">
          <img
            src={product.image}
            alt={product.name}
            className={`w-full h-full object-cover transition-transform duration-500 ${
              isOutOfStock ? 'grayscale' : 'group-hover:scale-105'
            }`}
          />
          
          {/* Out of Stock Overlay */}
          {isOutOfStock && (
            <div className="absolute inset-0 bg-background/70 flex items-center justify-center">
              <Badge variant="secondary" className="bg-destructive/90 text-destructive-foreground text-sm px-4 py-1">
                Out of Stock
              </Badge>
            </div>
          )}
          
          {/* Badges */}
          {!isOutOfStock && (
            <div className="absolute top-3 left-3 flex flex-col gap-2">
              {product.badge && (
                <Badge className="bg-primary text-primary-foreground text-xs">
                  {product.badge}
                </Badge>
              )}
              {discount > 0 && (
                <Badge variant="destructive" className="text-xs">
                  -{discount}%
                </Badge>
              )}
            </div>
          )}

          {/* Quick Actions */}
          <div className="absolute top-3 right-3 flex flex-col gap-2 opacity-0 translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300">
            <Button
              size="icon"
              variant="secondary"
              className={`h-8 w-8 rounded-full backdrop-blur-sm shadow-md transition-colors ${
                inWishlist 
                  ? 'bg-destructive/90 text-destructive-foreground hover:bg-destructive' 
                  : 'bg-background/90 hover:bg-primary hover:text-primary-foreground'
              }`}
              onClick={handleToggleWishlist}
            >
              <Heart className={`h-4 w-4 ${inWishlist ? 'fill-current' : ''}`} />
            </Button>
            <Button
              size="icon"
              variant="secondary"
              className="h-8 w-8 rounded-full bg-background/90 backdrop-blur-sm hover:bg-primary hover:text-primary-foreground shadow-md"
            >
              <Eye className="h-4 w-4" />
            </Button>
          </div>

          {/* Add to Cart Button */}
          {!isOutOfStock && (
            <div className="absolute bottom-0 left-0 right-0 p-3 translate-y-full group-hover:translate-y-0 transition-transform duration-300">
              <Button
                onClick={handleAddToCart}
                className="w-full bg-primary hover:bg-primary-dark text-primary-foreground shadow-lg"
              >
                <ShoppingCart className="h-4 w-4 mr-2" />
                Add to Cart
              </Button>
            </div>
          )}
        </div>

        {/* Content */}
        <CardContent className="p-4">
          <div className="space-y-2">
            {/* Category */}
            <p className="text-xs text-muted-foreground uppercase tracking-wide">
              {product.category}
            </p>
            
            {/* Title */}
            <h3 className={`font-medium text-sm line-clamp-2 transition-colors ${
              isOutOfStock ? 'text-muted-foreground' : 'text-foreground group-hover:text-primary'
            }`}>
              {product.name}
            </h3>

            {/* Rating */}
            <div className="flex items-center gap-1">
              <div className="flex items-center">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    className={`h-3 w-3 ${
                      i < Math.floor(product.rating)
                        ? 'text-warning fill-warning'
                        : 'text-muted-foreground'
                    }`}
                  />
                ))}
              </div>
              <span className="text-xs text-muted-foreground">
                ({product.reviews})
              </span>
            </div>

            {/* Price */}
            <div className="flex items-center gap-2 pt-1">
              <span className={`font-heading font-bold text-lg ${
                isOutOfStock ? 'text-muted-foreground' : 'text-foreground'
              }`}>
                {formatPrice(product.price)}
              </span>
              {product.originalPrice && (
                <span className="text-sm text-muted-foreground line-through">
                  {formatPrice(product.originalPrice)}
                </span>
              )}
            </div>

            {/* Stock Status */}
            {isOutOfStock && (
              <p className="text-xs text-destructive font-medium">
                Currently unavailable
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
};

export default ProductCard;
