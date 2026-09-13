import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Laptop, 
  Shirt, 
  Home, 
  Apple, 
  Sparkles, 
  Dumbbell, 
  ChevronRight,
  Grid3X3,
  X,
  Loader2
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { ScrollArea } from '../ui/scroll-area';
import { Badge } from '../ui/badge';
import { Separator } from '../ui/separator';
import ProductService from '../../services/productService';

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

const CategoriesModal = ({ trigger, open, onOpenChange }) => {
  const [categories, setCategories] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [isOpen, setIsOpen] = useState(false);

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

  const handleOpenChange = (newOpen) => {
    setIsOpen(newOpen);
    if (onOpenChange) onOpenChange(newOpen);
    if (!newOpen) {
      setSelectedCategory(null);
    }
  };

  const actualOpen = open !== undefined ? open : isOpen;

  return (
    <Dialog open={actualOpen} onOpenChange={handleOpenChange}>
      {trigger && <DialogTrigger asChild>{trigger}</DialogTrigger>}
      <DialogContent className="max-w-4xl max-h-[85vh] p-0 gap-0 overflow-hidden">
        <DialogHeader className="px-6 py-4 border-b border-border bg-muted/30">
          <DialogTitle className="font-heading text-xl flex items-center gap-2">
            <Grid3X3 className="h-5 w-5 text-primary" />
            Browse All Categories
          </DialogTitle>
        </DialogHeader>
        
        <div className="flex h-[60vh]">
          {/* Categories List - Left Panel */}
          <ScrollArea className="w-1/3 border-r border-border">
            <div className="p-2">
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                </div>
              ) : (
                categories.map((category) => {
                  const IconComponent = getCategoryIcon(category.name);
                  const isSelected = selectedCategory?.id === category.id;
                  
                  return (
                    <button
                      key={category.id}
                      onClick={() => setSelectedCategory(category)}
                      className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition-all ${
                        isSelected 
                          ? 'bg-primary/10 border-l-4 border-primary' 
                          : 'hover:bg-muted border-l-4 border-transparent'
                      }`}
                    >
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 overflow-hidden ${
                        isSelected ? 'bg-primary/20' : 'bg-muted'
                      }`}>
                        {category.image ? (
                          <img src={category.image} alt={category.name} className="h-6 w-6 object-cover rounded" />
                        ) : (
                          <IconComponent className={`h-5 w-5 ${isSelected ? 'text-primary' : 'text-muted-foreground'}`} />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className={`font-medium text-sm truncate ${isSelected ? 'text-primary' : 'text-foreground'}`}>
                          {category.name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {category.product_count || 0} products
                        </p>
                      </div>
                      <ChevronRight className={`h-4 w-4 shrink-0 ${isSelected ? 'text-primary' : 'text-muted-foreground'}`} />
                    </button>
                  );
                })
              )}
            </div>
          </ScrollArea>

          {/* Subcategories - Right Panel */}
          <div className="flex-1 bg-background">
            {selectedCategory ? (
              <ScrollArea className="h-full">
                <div className="p-6">
                  {/* Category Header */}
                  <div className="mb-6">
                    <div className="flex items-center gap-3 mb-2">
                      {(() => {
                        const IconComponent = getCategoryIcon(selectedCategory.name);
                        return (
                          <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center overflow-hidden">
                            {selectedCategory.image ? (
                              <img src={selectedCategory.image} alt={selectedCategory.name} className="h-8 w-8 object-cover rounded" />
                            ) : (
                              <IconComponent className="h-6 w-6 text-primary" />
                            )}
                          </div>
                        );
                      })()}
                      <div>
                        <h3 className="font-heading text-lg font-semibold text-foreground">
                          {selectedCategory.name}
                        </h3>
                        <p className="text-sm text-muted-foreground">
                          {selectedCategory.description || `Browse ${selectedCategory.name} products`}
                        </p>
                      </div>
                    </div>
                    <Link 
                      to={`/store?category=${selectedCategory.id}`}
                      onClick={() => handleOpenChange(false)}
                    >
                      <Button variant="outline" size="sm" className="mt-2">
                        View All {selectedCategory.name}
                        <ChevronRight className="ml-1 h-4 w-4" />
                      </Button>
                    </Link>
                  </div>

                  <Separator className="mb-6" />

                  {/* Subcategories Grid */}
                  {selectedCategory.subcategories && selectedCategory.subcategories.length > 0 ? (
                    <div>
                      <h4 className="text-sm font-medium text-muted-foreground mb-4">
                        Subcategories
                      </h4>
                      <div className="grid grid-cols-2 gap-3">
                        {selectedCategory.subcategories.map((sub) => (
                          <Link
                            key={sub.id}
                            to={`/store?category=${sub.id}`}
                            onClick={() => handleOpenChange(false)}
                            className="group flex items-center justify-between p-4 rounded-xl border border-border hover:border-primary/50 hover:bg-primary/5 transition-all"
                          >
                            <div>
                              <p className="font-medium text-sm text-foreground group-hover:text-primary transition-colors">
                                {sub.name}
                              </p>
                              <p className="text-xs text-muted-foreground mt-0.5">
                                {sub.product_count || 0} items
                              </p>
                            </div>
                            <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                          </Link>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <p className="text-sm text-muted-foreground">
                        No subcategories available. Browse all products in this category.
                      </p>
                    </div>
                  )}
                </div>
              </ScrollArea>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center p-6">
                <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
                  <Grid3X3 className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="font-heading text-lg font-semibold text-foreground mb-2">
                  Select a Category
                </h3>
                <p className="text-sm text-muted-foreground max-w-xs">
                  Choose a category from the left to view its subcategories and browse products.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Footer with quick links */}
        <div className="px-6 py-4 border-t border-border bg-muted/30">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              {categories.length} categories • {categories.reduce((acc, cat) => acc + (cat.product_count || 0), 0)}+ products
            </p>
            <Link to="/store" onClick={() => handleOpenChange(false)}>
              <Button size="sm" className="bg-primary hover:bg-primary-dark">
                Browse All Products
                <ChevronRight className="ml-1 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default CategoriesModal;
