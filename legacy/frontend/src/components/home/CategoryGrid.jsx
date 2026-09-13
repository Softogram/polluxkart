import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Laptop, Shirt, Home, Apple, Sparkles, Dumbbell, Grid3X3, Loader2 } from 'lucide-react';
import { Card, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import ProductService from '../../services/productService';
import CategoriesModal from './CategoriesModal';

const iconMap = {
  Laptop,
  Shirt,
  Home,
  Apple,
  Sparkles,
  Dumbbell,
};

// Get icon based on category name
const getCategoryIcon = (categoryName) => {
  const name = categoryName?.toLowerCase() || '';
  if (name.includes('electronic')) return Laptop;
  if (name.includes('fashion') || name.includes('cloth')) return Shirt;
  if (name.includes('home') || name.includes('living')) return Home;
  if (name.includes('grocer') || name.includes('food')) return Apple;
  if (name.includes('beauty') || name.includes('cosmetic')) return Sparkles;
  if (name.includes('sport') || name.includes('fitness')) return Dumbbell;
  return Laptop;
};

const CategoryGrid = () => {
  const [categories, setCategories] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadCategories = async () => {
      try {
        const data = await ProductService.getCategories();
        setCategories(data || []);
      } catch (error) {
        console.error('Failed to load categories:', error);
        setCategories([]);
      } finally {
        setIsLoading(false);
      }
    };
    loadCategories();
  }, []);

  if (isLoading) {
    return (
      <section className="py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </section>
    );
  }

  return (
    <section id="categories-section" className="py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto scroll-mt-20">
      <div className="flex items-center justify-between mb-10">
        <div className="text-center sm:text-left">
          <h2 className="font-heading text-3xl font-bold text-foreground">Shop by Category</h2>
          <p className="text-muted-foreground mt-2">Explore our wide range of products</p>
        </div>
        <CategoriesModal 
          trigger={
            <Button variant="outline" className="hidden sm:flex items-center gap-2">
              <Grid3X3 className="h-4 w-4" />
              View All
            </Button>
          }
        />
      </div>
      
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {categories.slice(0, 6).map((category, index) => {
          const IconComponent = getCategoryIcon(category.name);
          return (
            <Link
              key={category.id}
              to={`/store?category=${category.id}`}
              className="group"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <Card className="h-full border-border/50 bg-gradient-to-b from-card to-muted/30 hover:border-primary/50 hover:shadow-lg transition-all duration-300 overflow-hidden">
                <CardContent className="p-4 sm:p-6 flex flex-col items-center text-center">
                  <div className="w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center mb-3 group-hover:bg-primary/20 group-hover:scale-110 transition-all duration-300 overflow-hidden">
                    {category.image ? (
                      <img src={category.image} alt={category.name} className="h-8 w-8 object-cover rounded" />
                    ) : (
                      <IconComponent className="h-7 w-7 text-primary" />
                    )}
                  </div>
                  <h3 className="font-medium text-sm text-foreground group-hover:text-primary transition-colors">
                    {category.name}
                  </h3>
                  <p className="text-xs text-muted-foreground mt-1">
                    {category.product_count || 0} Products
                  </p>
                  <div className="mt-3 flex items-center text-xs text-primary opacity-0 group-hover:opacity-100 transition-opacity">
                    Explore <ArrowRight className="ml-1 h-3 w-3" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>

      {/* Mobile View All Button */}
      <div className="mt-6 sm:hidden flex justify-center">
        <CategoriesModal 
          trigger={
            <Button variant="outline" className="flex items-center gap-2">
              <Grid3X3 className="h-4 w-4" />
              View All Categories
            </Button>
          }
        />
      </div>
    </section>
  );
};

export default CategoryGrid;
