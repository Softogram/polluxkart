import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  Star,
  ShoppingCart,
  Heart,
  Share2,
  Truck,
  Shield,
  RotateCcw,
  Check,
  Minus,
  Plus,
  ChevronRight,
  Loader2,
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Progress } from '../components/ui/progress';
import { Separator } from '../components/ui/separator';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '../components/ui/breadcrumb';
import { useCart } from '../context/CartContext';
import { useWishlist } from '../context/WishlistContext';
import ProductService from '../services/productService';
import ProductCard from '../components/products/ProductCard';
import ReviewForm from '../components/products/ReviewForm';
import { formatPrice } from '../utils/currency';
import { toast } from 'sonner';

const ProductPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addToCart } = useCart();
  const { isInWishlist, toggleWishlist } = useWishlist();
  
  const [product, setProduct] = useState(null);
  const [relatedProducts, setRelatedProducts] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedImage, setSelectedImage] = useState(0);
  const [quantity, setQuantity] = useState(1);
  
  const inWishlist = product ? isInWishlist(product.id) : false;

  // Load product data
  useEffect(() => {
    // Mock reviews data (fallback) - defined inside effect to avoid dependency warning
    const fallbackReviews = [
      {
        id: 1,
        user_name: 'Sarah M.',
        user_avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah',
        rating: 5,
        created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        title: 'Absolutely amazing product!',
        comment: 'Exceeded my expectations in every way. The quality is outstanding and it arrived quickly.',
        helpful_count: 24,
      },
      {
        id: 2,
        user_name: 'James K.',
        user_avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=James',
        rating: 4,
        created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
        title: 'Great value for money',
        comment: 'Very happy with this purchase. Works exactly as described. Would recommend to others.',
        helpful_count: 18,
      },
      {
        id: 3,
        user_name: 'Emily R.',
        user_avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Emily',
        rating: 5,
        created_at: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
        title: 'Perfect!',
        comment: 'This is exactly what I was looking for. The design is sleek and the functionality is top-notch.',
        helpful_count: 31,
      },
    ];

    const loadProduct = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const productData = await ProductService.getProductById(id);
        
        // Transform to frontend format
        const transformedProduct = {
          id: productData.id,
          name: productData.name,
          category: productData.category_name || 'General',
          categoryId: productData.category_id,
          price: productData.price,
          originalPrice: productData.original_price,
          rating: productData.rating || 4.5,
          reviews: productData.review_count || 0,
          image: productData.image || (productData.images && productData.images[0]) || 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500',
          images: productData.images?.length > 0 ? productData.images : [productData.image || 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500'],
          description: productData.description || '',
          features: productData.features || [],
          inStock: productData.in_stock !== false && productData.stock > 0,
          stock: productData.stock,
          badge: productData.original_price && productData.original_price > productData.price ? 'Sale' : null,
          brand: productData.brand,
        };
        
        setProduct(transformedProduct);
        
        // Load related products
        if (transformedProduct.categoryId) {
          const relatedResponse = await ProductService.getProducts({
            categoryId: transformedProduct.categoryId,
            pageSize: 5,
          });
          const related = (relatedResponse.products || [])
            .filter(p => p.id !== id)
            .slice(0, 4)
            .map(p => ({
              id: p.id,
              name: p.name,
              category: p.category_name || 'General',
              price: p.price,
              originalPrice: p.original_price,
              rating: p.rating || 0,
              reviews: p.review_count || 0,
              image: p.image || (p.images && p.images[0]),
              inStock: p.in_stock !== false,
              badge: p.original_price && p.original_price > p.price ? 'Sale' : null,
            }));
          setRelatedProducts(related);
        }

        // Load reviews
        try {
          const reviewsData = await ProductService.getProductReviews(id);
          setReviews(reviewsData || []);
        } catch (reviewErr) {
          console.error('Failed to load reviews:', reviewErr);
          // Use mock reviews as fallback
          setReviews(fallbackReviews);
        }
      } catch (err) {
        console.error('Failed to load product:', err);
        setError('Product not found');
      } finally {
        setIsLoading(false);
      }
    };

    loadProduct();
  }, [id]);

  // Function to reload reviews after a new review is submitted
  const reloadReviews = async () => {
    try {
      const reviewsData = await ProductService.getProductReviews(id);
      setReviews(reviewsData || []);
      // Also update the product review count
      if (product) {
        setProduct(prev => ({
          ...prev,
          reviews: (reviewsData?.length || 0)
        }));
      }
    } catch (err) {
      console.error('Failed to reload reviews:', err);
    }
  };

  // Mock reviews data for display fallback
  const mockReviews = [
    {
      id: 1,
      user_name: 'Sarah M.',
      user_avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah',
      rating: 5,
      created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      title: 'Absolutely amazing product!',
      comment: 'Exceeded my expectations in every way. The quality is outstanding and it arrived quickly.',
      helpful_count: 24,
    },
    {
      id: 2,
      user_name: 'James K.',
      user_avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=James',
      rating: 4,
      created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      title: 'Great value for money',
      comment: 'Very happy with this purchase. Works exactly as described. Would recommend to others.',
      helpful_count: 18,
    },
    {
      id: 3,
      user_name: 'Emily R.',
      user_avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Emily',
      rating: 5,
      created_at: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
      title: 'Perfect!',
      comment: 'This is exactly what I was looking for. The design is sleek and the functionality is top-notch.',
      helpful_count: 31,
    },
  ];

  const ratingBreakdown = [
    { stars: 5, percentage: 72 },
    { stars: 4, percentage: 18 },
    { stars: 3, percentage: 6 },
    { stars: 2, percentage: 3 },
    { stars: 1, percentage: 1 },
  ];

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} week${Math.floor(diffDays / 7) > 1 ? 's' : ''} ago`;
    return `${Math.floor(diffDays / 30)} month${Math.floor(diffDays / 30) > 1 ? 's' : ''} ago`;
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-2 text-muted-foreground">Loading product...</span>
      </div>
    );
  }

  // Error state
  if (error || !product) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="text-center p-8">
          <h2 className="font-heading text-2xl font-bold mb-4">Product Not Found</h2>
          <p className="text-muted-foreground mb-6">The product you're looking for doesn't exist.</p>
          <Button onClick={() => navigate('/store')}>Back to Store</Button>
        </Card>
      </div>
    );
  }

  const isOutOfStock = !product.inStock;

  const discount = product.originalPrice
    ? Math.round(((product.originalPrice - product.price) / product.originalPrice) * 100)
    : 0;

  const handleAddToCart = () => {
    if (isOutOfStock) {
      toast.error('This item is currently out of stock');
      return;
    }
    addToCart(product, quantity);
    toast.success(`${quantity}x ${product.name} added to cart!`);
  };

  const handleBuyNow = () => {
    if (isOutOfStock) {
      toast.error('This item is currently out of stock');
      return;
    }
    addToCart(product, quantity);
    navigate('/checkout');
  };

  const displayReviews = reviews.length > 0 ? reviews : mockReviews;

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
              <BreadcrumbLink asChild>
                <Link to="/store">Store</Link>
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage className="capitalize">{product.category}</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>

        {/* Product Details */}
        <div className="grid lg:grid-cols-2 gap-8 lg:gap-12 mb-16">
          {/* Image Gallery */}
          <div className="space-y-4">
            {/* Main Image */}
            <div className="relative aspect-square rounded-2xl overflow-hidden bg-muted/30 border border-border">
              <img
                src={product.images[selectedImage]}
                alt={product.name}
                className="w-full h-full object-cover"
              />
              {product.badge && (
                <Badge className="absolute top-4 left-4 bg-primary text-primary-foreground">
                  {product.badge}
                </Badge>
              )}
              {discount > 0 && (
                <Badge variant="destructive" className="absolute top-4 right-4">
                  -{discount}% OFF
                </Badge>
              )}
            </div>

            {/* Thumbnail Gallery */}
            {product.images.length > 1 && (
              <div className="flex gap-3 overflow-x-auto pb-2">
                {product.images.map((image, index) => (
                  <button
                    key={index}
                    onClick={() => setSelectedImage(index)}
                    className={`shrink-0 w-20 h-20 rounded-lg overflow-hidden border-2 transition-all ${
                      selectedImage === index
                        ? 'border-primary ring-2 ring-primary/20'
                        : 'border-border hover:border-primary/50'
                    }`}
                  >
                    <img
                      src={image}
                      alt={`${product.name} ${index + 1}`}
                      className="w-full h-full object-cover"
                    />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Product Info */}
          <div className="space-y-6">
            {/* Category & Title */}
            <div>
              <p className="text-sm text-primary uppercase tracking-wide font-medium mb-2">
                {product.category}
              </p>
              <h1 className="font-heading text-3xl lg:text-4xl font-bold text-foreground">
                {product.name}
              </h1>
              {product.brand && (
                <p className="text-sm text-muted-foreground mt-1">by {product.brand}</p>
              )}
            </div>

            {/* Rating */}
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    className={`h-5 w-5 ${
                      i < Math.floor(product.rating)
                        ? 'text-warning fill-warning'
                        : 'text-muted-foreground'
                    }`}
                  />
                ))}
              </div>
              <span className="text-sm text-muted-foreground">
                {product.rating} ({product.reviews.toLocaleString()} reviews)
              </span>
            </div>

            {/* Price */}
            <div className="flex items-baseline gap-3">
              <span className="font-heading text-4xl font-bold text-foreground">
                {formatPrice(product.price)}
              </span>
              {product.originalPrice && (
                <span className="text-xl text-muted-foreground line-through">
                  {formatPrice(product.originalPrice)}
                </span>
              )}
              {discount > 0 && (
                <Badge variant="secondary" className="bg-success/10 text-success">
                  Save {formatPrice(product.originalPrice - product.price)}
                </Badge>
              )}
            </div>

            {/* Description */}
            <p className="text-muted-foreground leading-relaxed">
              {product.description}
            </p>

            {/* Features */}
            {product.features.length > 0 && (
              <div className="space-y-2">
                <p className="font-medium text-foreground">Key Features:</p>
                <ul className="grid grid-cols-2 gap-2">
                  {product.features.map((feature, index) => (
                    <li key={index} className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Check className="h-4 w-4 text-success" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <Separator />

            {/* Quantity & Add to Cart */}
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <span className="font-medium">Quantity:</span>
                <div className="flex items-center border rounded-lg">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="rounded-r-none"
                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                    disabled={isOutOfStock}
                  >
                    <Minus className="h-4 w-4" />
                  </Button>
                  <span className="w-12 text-center font-medium">{quantity}</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="rounded-l-none"
                    onClick={() => setQuantity(quantity + 1)}
                    disabled={isOutOfStock}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                {product.stock > 0 && product.stock <= 10 && (
                  <span className="text-sm text-warning">Only {product.stock} left!</span>
                )}
              </div>

              {/* Out of Stock Notice */}
              {isOutOfStock && (
                <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20">
                  <p className="text-destructive font-medium flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-destructive"></span>
                    Currently Out of Stock
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    This item is not available for purchase at the moment.
                  </p>
                </div>
              )}

              <div className="flex flex-col sm:flex-row gap-3">
                <Button
                  size="lg"
                  className={`flex-1 ${isOutOfStock ? 'opacity-50 cursor-not-allowed' : 'bg-primary hover:bg-primary-dark shadow-lg shadow-primary/25'}`}
                  onClick={handleAddToCart}
                  disabled={isOutOfStock}
                  data-testid="add-to-cart-btn"
                >
                  <ShoppingCart className="mr-2 h-5 w-5" />
                  {isOutOfStock ? 'Out of Stock' : 'Add to Cart'}
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  className={`flex-1 ${isOutOfStock ? 'opacity-50 cursor-not-allowed' : ''}`}
                  onClick={handleBuyNow}
                  disabled={isOutOfStock}
                  data-testid="buy-now-btn"
                >
                  Buy Now
                </Button>
              </div>

              <div className="flex gap-4">
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => {
                    const added = toggleWishlist(product);
                    if (added) {
                      toast.success('Added to wishlist!');
                    } else {
                      toast.success('Removed from wishlist');
                    }
                  }}
                  className={inWishlist ? 'text-destructive hover:text-destructive' : ''}
                  data-testid="wishlist-btn"
                >
                  <Heart className={`mr-2 h-4 w-4 ${inWishlist ? 'fill-current' : ''}`} />
                  {inWishlist ? 'In Wishlist' : 'Add to Wishlist'}
                </Button>
                <Button variant="ghost" size="sm" onClick={() => {
                  navigator.clipboard.writeText(window.location.href);
                  toast.success('Link copied!');
                }}>
                  <Share2 className="mr-2 h-4 w-4" />
                  Share
                </Button>
              </div>
            </div>

            {/* Trust Badges */}
            <div className="grid grid-cols-3 gap-4 pt-4">
              <div className="text-center p-3 rounded-lg bg-muted/50">
                <Truck className="h-5 w-5 mx-auto text-primary mb-1" />
                <p className="text-xs text-muted-foreground">Free Shipping</p>
              </div>
              <div className="text-center p-3 rounded-lg bg-muted/50">
                <Shield className="h-5 w-5 mx-auto text-primary mb-1" />
                <p className="text-xs text-muted-foreground">Secure Payment</p>
              </div>
              <div className="text-center p-3 rounded-lg bg-muted/50">
                <RotateCcw className="h-5 w-5 mx-auto text-primary mb-1" />
                <p className="text-xs text-muted-foreground">30-Day Returns</p>
              </div>
            </div>
          </div>
        </div>

        {/* Product Details Tabs */}
        <Tabs defaultValue="reviews" className="mb-16">
          <TabsList className="w-full justify-start border-b rounded-none bg-transparent h-auto p-0 mb-6">
            <TabsTrigger
              value="description"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-6 py-3"
            >
              Description
            </TabsTrigger>
            <TabsTrigger
              value="specifications"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-6 py-3"
            >
              Specifications
            </TabsTrigger>
            <TabsTrigger
              value="reviews"
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-6 py-3"
            >
              Reviews ({product.reviews})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="description" className="mt-0">
            <Card>
              <CardContent className="p-6">
                <div className="prose prose-sm max-w-none text-muted-foreground">
                  <p>{product.description}</p>
                  <p className="mt-4">
                    Experience premium quality with our carefully crafted products. Each item is designed with attention to detail and built to last. We use only the finest materials to ensure durability and performance.
                  </p>
                  <h4 className="text-foreground font-medium mt-6 mb-3">What's in the Box:</h4>
                  <ul className="list-disc pl-5 space-y-1">
                    <li>1x {product.name}</li>
                    <li>User Manual</li>
                    <li>Warranty Card</li>
                    <li>Premium Packaging</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="specifications" className="mt-0">
            <Card>
              <CardContent className="p-6">
                <div className="grid sm:grid-cols-2 gap-4">
                  {product.features.map((feature, index) => (
                    <div key={index} className="flex justify-between py-3 border-b border-border last:border-0">
                      <span className="text-muted-foreground">Feature {index + 1}</span>
                      <span className="font-medium text-foreground">{feature}</span>
                    </div>
                  ))}
                  <div className="flex justify-between py-3 border-b border-border">
                    <span className="text-muted-foreground">Category</span>
                    <span className="font-medium text-foreground capitalize">{product.category}</span>
                  </div>
                  {product.brand && (
                    <div className="flex justify-between py-3 border-b border-border">
                      <span className="text-muted-foreground">Brand</span>
                      <span className="font-medium text-foreground">{product.brand}</span>
                    </div>
                  )}
                  <div className="flex justify-between py-3 border-b border-border">
                    <span className="text-muted-foreground">Availability</span>
                    <span className={`font-medium ${product.inStock ? 'text-success' : 'text-destructive'}`}>
                      {product.inStock ? 'In Stock' : 'Out of Stock'}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="reviews" className="mt-0">
            <div className="grid lg:grid-cols-3 gap-6">
              {/* Rating Summary */}
              <Card>
                <CardContent className="p-6">
                  <div className="text-center mb-6">
                    <div className="font-heading text-5xl font-bold text-foreground">
                      {product.rating.toFixed(1)}
                    </div>
                    <div className="flex justify-center gap-1 my-2">
                      {[...Array(5)].map((_, i) => (
                        <Star
                          key={i}
                          className={`h-5 w-5 ${
                            i < Math.floor(product.rating)
                              ? 'text-warning fill-warning'
                              : 'text-muted-foreground'
                          }`}
                        />
                      ))}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Based on {product.reviews.toLocaleString()} reviews
                    </p>
                  </div>

                  <div className="space-y-3">
                    {ratingBreakdown.map((item) => (
                      <div key={item.stars} className="flex items-center gap-3">
                        <span className="text-sm w-3">{item.stars}</span>
                        <Star className="h-4 w-4 text-warning fill-warning" />
                        <Progress value={item.percentage} className="h-2 flex-1" />
                        <span className="text-sm text-muted-foreground w-10">
                          {item.percentage}%
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Reviews List */}
              <div className="lg:col-span-2 space-y-4">
                {/* Write Review Form */}
                <ReviewForm 
                  productId={product.id} 
                  productName={product.name}
                  onReviewSubmitted={reloadReviews}
                />

                {/* Existing Reviews */}
                <div className="mt-6">
                  <h3 className="font-semibold text-lg mb-4">Customer Reviews</h3>
                  {displayReviews.length === 0 ? (
                    <Card>
                      <CardContent className="p-6 text-center text-muted-foreground">
                        No reviews yet. Be the first to review this product!
                      </CardContent>
                    </Card>
                  ) : (
                    displayReviews.map((review) => (
                      <Card key={review.id} className="mb-4">
                        <CardContent className="p-6">
                          <div className="flex items-start gap-4">
                            <Avatar>
                              <AvatarImage src={review.user_avatar} />
                              <AvatarFallback>{(review.user_name || 'U')[0]}</AvatarFallback>
                            </Avatar>
                            <div className="flex-1">
                              <div className="flex items-center justify-between mb-2">
                                <div>
                                  <p className="font-medium text-foreground">{review.user_name}</p>
                                  <p className="text-xs text-muted-foreground">{formatDate(review.created_at)}</p>
                                </div>
                                <div className="flex gap-0.5">
                                  {[...Array(5)].map((_, i) => (
                                    <Star
                                      key={i}
                                      className={`h-4 w-4 ${
                                        i < review.rating
                                          ? 'text-warning fill-warning'
                                          : 'text-muted-foreground'
                                      }`}
                                    />
                                  ))}
                                </div>
                              </div>
                              {review.title && (
                                <h4 className="font-medium text-foreground mb-1">{review.title}</h4>
                              )}
                              <p className="text-sm text-muted-foreground">{review.comment}</p>
                              <div className="mt-3 flex items-center gap-2">
                                <Button variant="ghost" size="sm" className="text-xs">
                                  Helpful ({review.helpful_count || 0})
                                </Button>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))
                  )}
                </div>

                {displayReviews.length > 3 && (
                  <Button variant="outline" className="w-full">
                    Load More Reviews
                  </Button>
                )}
              </div>
            </div>
          </TabsContent>
        </Tabs>

        {/* Related Products */}
        {relatedProducts.length > 0 && (
          <section>
            <div className="flex items-center justify-between mb-6">
              <h2 className="font-heading text-2xl font-bold text-foreground">Related Products</h2>
              <Link to={`/store?category=${product.categoryId}`}>
                <Button variant="ghost" className="text-primary">
                  View All <ChevronRight className="ml-1 h-4 w-4" />
                </Button>
              </Link>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6">
              {relatedProducts.map((p) => (
                <ProductCard key={p.id} product={p} />
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
};

export default ProductPage;
