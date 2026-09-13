import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, TrendingUp } from 'lucide-react';
import { Button } from '../ui/button';
import ProductCard from '../products/ProductCard';
import { products } from '../../data/products';

const FeaturedProducts = () => {
  // Get products with badges or high ratings
  const featuredProducts = products
    .filter(p => p.badge || p.rating >= 4.7)
    .slice(0, 8);

  return (
    <section className="py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-accent/20">
            <TrendingUp className="h-5 w-5 text-accent" />
          </div>
          <div>
            <h2 className="font-heading text-2xl font-bold text-foreground">Featured Products</h2>
            <p className="text-sm text-muted-foreground">Handpicked items just for you</p>
          </div>
        </div>
        <Link to="/store">
          <Button variant="ghost" className="text-primary hover:text-primary-dark hover:bg-primary/10">
            View All
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6">
        {featuredProducts.map((product, index) => (
          <div
            key={product.id}
            className="animate-fade-in"
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <ProductCard product={product} />
          </div>
        ))}
      </div>
    </section>
  );
};

export default FeaturedProducts;
