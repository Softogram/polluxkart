import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Truck, Shield, CreditCard, Headphones } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import PromotionBanner from '../components/home/PromotionBanner';
import CategoryGrid from '../components/home/CategoryGrid';
import FeaturedProducts from '../components/home/FeaturedProducts';
import CategoriesModal from '../components/home/CategoriesModal';
import { products } from '../data/products';
import ProductCard from '../components/products/ProductCard';

const HomePage = () => {
  const newArrivals = products.filter(p => p.badge === 'New' || p.badge === 'Premium').slice(0, 4);
  const bestSellers = products.filter(p => p.rating >= 4.7).slice(0, 4);

  const features = [
    {
      icon: Truck,
      title: 'Free Shipping',
      description: 'On orders over $100',
    },
    {
      icon: Shield,
      title: 'Secure Payment',
      description: '100% secure transactions',
    },
    {
      icon: CreditCard,
      title: 'Easy Returns',
      description: '30-day return policy',
    },
    {
      icon: Headphones,
      title: '24/7 Support',
      description: 'Dedicated customer service',
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary/5 via-background to-accent/5">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-80 h-80 rounded-full bg-primary/10 blur-3xl" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 rounded-full bg-accent/10 blur-3xl" />
        </div>
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 lg:py-24">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left Content */}
            <div className="text-left space-y-6">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium">
                <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
                New Collection Available
              </div>
              
              <h1 className="font-heading text-4xl sm:text-5xl lg:text-6xl font-bold text-foreground leading-tight">
                Discover Amazing
                <span className="text-gradient block">Products</span>
              </h1>
              
              <p className="text-lg text-muted-foreground max-w-lg">
                Your one-stop destination for electronics, fashion, home essentials, and more. 
                Quality products at unbeatable prices.
              </p>
              
              <div className="flex flex-wrap gap-4">
                <Link to="/store">
                  <Button size="lg" className="bg-primary hover:bg-primary-dark text-primary-foreground shadow-lg shadow-primary/25">
                    Shop Now
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Button>
                </Link>
                <CategoriesModal 
                  trigger={
                    <Button size="lg" variant="outline" className="border-primary/30 hover:bg-primary/5">
                      Explore Categories
                    </Button>
                  }
                />
              </div>

              {/* Stats */}
              <div className="flex gap-8 pt-4">
                <div>
                  <p className="font-heading text-3xl font-bold text-foreground">10K+</p>
                  <p className="text-sm text-muted-foreground">Products</p>
                </div>
                <div>
                  <p className="font-heading text-3xl font-bold text-foreground">50K+</p>
                  <p className="text-sm text-muted-foreground">Customers</p>
                </div>
                <div>
                  <p className="font-heading text-3xl font-bold text-foreground">4.9</p>
                  <p className="text-sm text-muted-foreground">Rating</p>
                </div>
              </div>
            </div>

            {/* Right Content - Hero Image */}
            <div className="relative lg:h-[500px] flex items-center justify-center">
              <div className="relative w-full max-w-md">
                {/* Main Hero Image */}
                <div className="relative z-10 rounded-2xl overflow-hidden shadow-2xl">
                  <img
                    src="https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800"
                    alt="Shopping Experience"
                    className="w-full h-[400px] object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-foreground/20 to-transparent" />
                </div>
                
                {/* Floating Cards */}
                <div className="absolute -left-8 top-1/4 z-20 animate-bounce-soft">
                  <Card className="shadow-lg border-0 bg-background/95 backdrop-blur">
                    <CardContent className="p-3 flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-success/20 flex items-center justify-center">
                        <Truck className="h-5 w-5 text-success" />
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Free Delivery</p>
                        <p className="text-sm font-medium">On $100+</p>
                      </div>
                    </CardContent>
                  </Card>
                </div>
                
                <div className="absolute -right-4 bottom-1/4 z-20 animate-bounce-soft" style={{ animationDelay: '0.5s' }}>
                  <Card className="shadow-lg border-0 bg-background/95 backdrop-blur">
                    <CardContent className="p-3 flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-warning/20 flex items-center justify-center">
                        <Shield className="h-5 w-5 text-warning" />
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Secure</p>
                        <p className="text-sm font-medium">Payment</p>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Promotions Section */}
      <PromotionBanner />

      {/* Category Grid */}
      <CategoryGrid />

      {/* Featured Products */}
      <FeaturedProducts />

      {/* New Arrivals */}
      <section className="py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="font-heading text-2xl font-bold text-foreground">New Arrivals</h2>
            <p className="text-sm text-muted-foreground">Fresh additions to our collection</p>
          </div>
          <Link to="/store">
            <Button variant="ghost" className="text-primary">
              View All <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6">
          {newArrivals.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      </section>

      {/* Features Section */}
      <section className="py-12 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <Card
                key={index}
                className="border-0 bg-background/80 backdrop-blur shadow-sm hover:shadow-md transition-shadow"
              >
                <CardContent className="p-6 text-center">
                  <div className="w-12 h-12 mx-auto rounded-xl bg-primary/10 flex items-center justify-center mb-4">
                    <feature.icon className="h-6 w-6 text-primary" />
                  </div>
                  <h3 className="font-medium text-foreground">{feature.title}</h3>
                  <p className="text-sm text-muted-foreground mt-1">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Best Sellers */}
      <section className="py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="font-heading text-2xl font-bold text-foreground">Best Sellers</h2>
            <p className="text-sm text-muted-foreground">Most loved by our customers</p>
          </div>
          <Link to="/store">
            <Button variant="ghost" className="text-primary">
              View All <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6">
          {bestSellers.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-primary/10 via-background to-accent/10">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="font-heading text-3xl sm:text-4xl font-bold text-foreground mb-4">
            Join the PolluxKart Family
          </h2>
          <p className="text-muted-foreground mb-8">
            Subscribe to get exclusive offers, early access to new products, and more!
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/auth">
              <Button size="lg" className="w-full sm:w-auto">
                Create Account
              </Button>
            </Link>
            <Link to="/store">
              <Button size="lg" variant="outline" className="w-full sm:w-auto">
                Start Shopping
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
