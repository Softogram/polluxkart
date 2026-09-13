import React, { useState, useMemo, useEffect, useCallback, useRef } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  Search,
  SlidersHorizontal,
  Grid3X3,
  LayoutList,
  X,
  ChevronLeft,
  ChevronRight,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Checkbox } from '../components/ui/checkbox';
import { Label } from '../components/ui/label';
import { Slider } from '../components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '../components/ui/sheet';
import { Separator } from '../components/ui/separator';
import { ScrollArea } from '../components/ui/scroll-area';
import { Alert, AlertDescription } from '../components/ui/alert';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '../components/ui/breadcrumb';
import ProductCard from '../components/products/ProductCard';
import ProductService from '../services/productService';

const ITEMS_PER_PAGE = 12;
const DEBOUNCE_DELAY = 500; // milliseconds

const StorePage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [viewMode, setViewMode] = useState('grid');
  const [priceRange, setPriceRange] = useState([0, 1500]);
  const [sortBy, setSortBy] = useState('default');
  const [currentPage, setCurrentPage] = useState(1);
  
  // Search state - simplified: only track input and debounced query
  const [searchInput, setSearchInput] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const debounceTimerRef = useRef(null);
  
  // API data state
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);
  const [totalProducts, setTotalProducts] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Selected filters
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedBrand, setSelectedBrand] = useState(null);

  // Initialize from URL params on mount
  useEffect(() => {
    const category = searchParams.get('category');
    const brand = searchParams.get('brand');
    const search = searchParams.get('search');
    const page = searchParams.get('page');
    
    if (category) setSelectedCategory(category);
    if (brand) setSelectedBrand(brand);
    if (search) {
      setSearchInput(search);
      setDebouncedSearch(search);
    }
    if (page) setCurrentPage(parseInt(page, 10));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run on mount

  // Debounce search input
  useEffect(() => {
    // Clear existing timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    
    // If empty, update immediately
    if (searchInput === '') {
      setDebouncedSearch('');
      return;
    }
    
    // Set new timer
    debounceTimerRef.current = setTimeout(() => {
      setDebouncedSearch(searchInput);
    }, DEBOUNCE_DELAY);
    
    // Cleanup on unmount or when searchInput changes
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [searchInput]);

  // Load categories and brands on mount
  useEffect(() => {
    const loadMetadata = async () => {
      try {
        const [categoriesData, brandsData] = await Promise.all([
          ProductService.getCategories(),
          ProductService.getBrands(),
        ]);
        setCategories(categoriesData || []);
        setBrands(brandsData || []);
      } catch (err) {
        console.error('Failed to load metadata:', err);
      }
    };
    loadMetadata();
  }, []);

  // Load products when filters change
  useEffect(() => {
    const loadProducts = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Map frontend sort values to backend API format
        const sortMap = {
          'default': 'default',
          'price-asc': 'price_asc',
          'price-desc': 'price_desc',
          'rating': 'rating',
          'newest': 'newest',
        };

        const response = await ProductService.getProducts({
          page: currentPage,
          pageSize: ITEMS_PER_PAGE,
          categoryId: selectedCategory,
          brand: selectedBrand,
          search: debouncedSearch || null,
          minPrice: priceRange[0] > 0 ? priceRange[0] : null,
          maxPrice: priceRange[1] < 1500 ? priceRange[1] : null,
          sortBy: sortMap[sortBy] || 'default',
        });

        // Transform API data to frontend format
        const transformedProducts = (response.products || []).map(product => ({
          id: product.id,
          name: product.name,
          category: product.category_name || 'General',
          price: product.price,
          originalPrice: product.original_price,
          rating: product.rating || 0,
          reviews: product.review_count || 0,
          image: product.image || (product.images && product.images[0]) || 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500',
          images: product.images || [],
          description: product.description || '',
          features: product.features || [],
          inStock: product.in_stock !== false,
          badge: product.original_price && product.original_price > product.price ? 'Sale' : null,
          brand: product.brand,
        }));

        setProducts(transformedProducts);
        setTotalProducts(response.total || 0);
        setTotalPages(response.total_pages || 1);
      } catch (err) {
        console.error('Failed to load products:', err);
        setError('Failed to load products. Please try again.');
        setProducts([]);
      } finally {
        setIsLoading(false);
      }
    };

    loadProducts();
  }, [currentPage, selectedCategory, selectedBrand, debouncedSearch, priceRange, sortBy]);

  // Handle search input change
  const handleSearchChange = useCallback((e) => {
    const value = e.target.value;
    setSearchInput(value);
    setCurrentPage(1); // Reset to first page when searching
  }, []);

  // Handle page change
  const handlePageChange = useCallback((page) => {
    setCurrentPage(page);
    setSearchParams((prev) => {
      prev.set('page', page.toString());
      return prev;
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [setSearchParams]);

  // Handle category toggle
  const handleCategoryChange = useCallback((categoryId) => {
    setSelectedCategory(prev => prev === categoryId ? null : categoryId);
    setCurrentPage(1);
  }, []);

  // Handle brand toggle
  const handleBrandChange = useCallback((brand) => {
    setSelectedBrand(prev => prev === brand ? null : brand);
    setCurrentPage(1);
  }, []);

  // Clear all filters
  const clearFilters = useCallback(() => {
    setSelectedCategory(null);
    setSelectedBrand(null);
    setPriceRange([0, 1500]);
    setSearchInput('');
    setDebouncedSearch('');
    setSortBy('default');
    setCurrentPage(1);
    setSearchParams({});
  }, [setSearchParams]);

  // Count active filters
  const activeFiltersCount = useMemo(() => {
    let count = 0;
    if (selectedCategory) count++;
    if (selectedBrand) count++;
    if (priceRange[0] > 0 || priceRange[1] < 1500) count++;
    if (debouncedSearch) count++;
    return count;
  }, [selectedCategory, selectedBrand, priceRange, debouncedSearch]);

  // Check if search is pending (input differs from debounced value)
  const isSearchPending = searchInput !== debouncedSearch;

  // Filter Sidebar Content
  const FilterContent = () => (
    <div className="space-y-6">
      {/* Search */}
      <div>
        <Label className="text-sm font-medium mb-3 block">Search</Label>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search products..."
            value={searchInput}
            onChange={handleSearchChange}
            className="pl-10"
            data-testid="store-search-input"
          />
          {isSearchPending && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            </div>
          )}
        </div>
        {searchInput && (
          <p className="text-xs text-muted-foreground mt-1">
            {isSearchPending ? 'Searching...' : `Showing results for "${debouncedSearch}"`}
          </p>
        )}
      </div>

      <Separator />

      {/* Brands */}
      {brands.length > 0 && (
        <>
          <div>
            <Label className="text-sm font-medium mb-3 block">Brands</Label>
            <div className="space-y-3 max-h-48 overflow-y-auto">
              {brands.map((brand) => (
                <div key={brand} className="flex items-center space-x-3">
                  <Checkbox
                    id={`brand-${brand}`}
                    checked={selectedBrand === brand}
                    onCheckedChange={() => handleBrandChange(brand)}
                  />
                  <Label
                    htmlFor={`brand-${brand}`}
                    className="text-sm font-normal cursor-pointer flex-1"
                  >
                    {brand}
                  </Label>
                </div>
              ))}
            </div>
          </div>
          <Separator />
        </>
      )}

      {/* Categories */}
      {categories.length > 0 && (
        <>
          <div>
            <Label className="text-sm font-medium mb-3 block">Categories</Label>
            <div className="space-y-3">
              {categories.map((category) => (
                <div key={category.id} className="flex items-center space-x-3">
                  <Checkbox
                    id={`category-${category.id}`}
                    checked={selectedCategory === category.id}
                    onCheckedChange={() => handleCategoryChange(category.id)}
                  />
                  <Label
                    htmlFor={`category-${category.id}`}
                    className="text-sm font-normal cursor-pointer flex-1 flex justify-between items-center"
                  >
                    <span>{category.name}</span>
                    {category.product_count > 0 && (
                      <span className="text-xs text-muted-foreground">
                        ({category.product_count})
                      </span>
                    )}
                  </Label>
                </div>
              ))}
            </div>
          </div>
          <Separator />
        </>
      )}

      {/* Price Range */}
      <div>
        <Label className="text-sm font-medium mb-4 block">Price Range</Label>
        <Slider
          value={priceRange}
          onValueChange={(value) => {
            setPriceRange(value);
            setCurrentPage(1);
          }}
          max={1500}
          step={10}
          className="mb-4"
        />
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>₹{priceRange[0]}</span>
          <span>₹{priceRange[1]}</span>
        </div>
      </div>

      <Separator />

      {/* Clear Filters */}
      {activeFiltersCount > 0 && (
        <Button
          variant="outline"
          className="w-full"
          onClick={clearFilters}
          data-testid="clear-filters-btn"
        >
          <X className="mr-2 h-4 w-4" />
          Clear All Filters ({activeFiltersCount})
        </Button>
      )}
    </div>
  );

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
              <BreadcrumbPage>Store</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>

        {/* Page Header */}
        <div className="mb-8">
          <h1 className="font-heading text-3xl font-bold text-foreground">All Products</h1>
          <p className="text-muted-foreground mt-1">
            {isLoading ? 'Loading...' : `Showing ${products.length} of ${totalProducts} products`}
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="flex gap-8">
          {/* Desktop Sidebar */}
          <aside className="hidden lg:block w-64 shrink-0">
            <Card className="sticky top-24">
              <CardContent className="p-6">
                <h2 className="font-heading font-semibold mb-6 flex items-center gap-2">
                  <SlidersHorizontal className="h-4 w-4" />
                  Filters
                </h2>
                <FilterContent />
              </CardContent>
            </Card>
          </aside>

          {/* Main Content */}
          <div className="flex-1">
            {/* Toolbar */}
            <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between mb-6">
              {/* Mobile Filter Button */}
              <Sheet>
                <SheetTrigger asChild>
                  <Button variant="outline" className="lg:hidden">
                    <SlidersHorizontal className="mr-2 h-4 w-4" />
                    Filters
                    {activeFiltersCount > 0 && (
                      <Badge className="ml-2 bg-primary text-primary-foreground">
                        {activeFiltersCount}
                      </Badge>
                    )}
                  </Button>
                </SheetTrigger>
                <SheetContent side="left" className="w-80">
                  <SheetHeader>
                    <SheetTitle>Filters</SheetTitle>
                  </SheetHeader>
                  <ScrollArea className="h-[calc(100vh-80px)] pr-4">
                    <div className="py-6">
                      <FilterContent />
                    </div>
                  </ScrollArea>
                </SheetContent>
              </Sheet>

              {/* Active Filters Tags */}
              <div className="flex flex-wrap gap-2">
                {selectedBrand && (
                  <Badge
                    variant="secondary"
                    className="cursor-pointer hover:bg-destructive/20"
                    onClick={() => setSelectedBrand(null)}
                    data-testid="active-brand-filter"
                  >
                    {selectedBrand}
                    <X className="ml-1 h-3 w-3" />
                  </Badge>
                )}
                {selectedCategory && categories.length > 0 && (
                  <Badge
                    variant="secondary"
                    className="cursor-pointer hover:bg-destructive/20"
                    onClick={() => setSelectedCategory(null)}
                    data-testid="active-category-filter"
                  >
                    {categories.find(c => c.id === selectedCategory)?.name}
                    <X className="ml-1 h-3 w-3" />
                  </Badge>
                )}
                {debouncedSearch && (
                  <Badge
                    variant="secondary"
                    className="cursor-pointer hover:bg-destructive/20"
                    onClick={() => {
                      setSearchInput('');
                      setDebouncedSearch('');
                    }}
                    data-testid="active-search-filter"
                  >
                    Search: {debouncedSearch}
                    <X className="ml-1 h-3 w-3" />
                  </Badge>
                )}
              </div>

              {/* Sort & View Options */}
              <div className="flex items-center gap-4 ml-auto">
                <Select value={sortBy} onValueChange={(value) => {
                  setSortBy(value);
                  setCurrentPage(1);
                }}>
                  <SelectTrigger className="w-[180px]" data-testid="sort-select">
                    <SelectValue placeholder="Sort by" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="default">Featured</SelectItem>
                    <SelectItem value="newest">Newest</SelectItem>
                    <SelectItem value="price-asc">Price: Low to High</SelectItem>
                    <SelectItem value="price-desc">Price: High to Low</SelectItem>
                    <SelectItem value="rating">Top Rated</SelectItem>
                  </SelectContent>
                </Select>

                <div className="hidden sm:flex items-center border rounded-lg">
                  <Button
                    variant="ghost"
                    size="icon"
                    className={`rounded-r-none ${viewMode === 'grid' ? 'bg-muted' : ''}`}
                    onClick={() => setViewMode('grid')}
                    data-testid="grid-view-btn"
                  >
                    <Grid3X3 className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className={`rounded-l-none ${viewMode === 'list' ? 'bg-muted' : ''}`}
                    onClick={() => setViewMode('list')}
                    data-testid="list-view-btn"
                  >
                    <LayoutList className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>

            {/* Loading State */}
            {isLoading ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <span className="ml-2 text-muted-foreground">Loading products...</span>
              </div>
            ) : products.length > 0 ? (
              <>
                {/* Products Grid */}
                <div
                  className={`grid gap-4 md:gap-6 ${
                    viewMode === 'grid'
                      ? 'grid-cols-2 sm:grid-cols-2 lg:grid-cols-3'
                      : 'grid-cols-1'
                  }`}
                  data-testid="products-grid"
                >
                  {products.map((product) => (
                    <ProductCard key={product.id} product={product} />
                  ))}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="mt-8 flex items-center justify-center gap-2" data-testid="pagination">
                    <Button
                      variant="outline"
                      size="icon"
                      disabled={currentPage === 1}
                      onClick={() => handlePageChange(currentPage - 1)}
                      data-testid="prev-page-btn"
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    
                    {[...Array(totalPages)].map((_, i) => {
                      const page = i + 1;
                      if (
                        page === 1 ||
                        page === totalPages ||
                        (page >= currentPage - 1 && page <= currentPage + 1)
                      ) {
                        return (
                          <Button
                            key={page}
                            variant={currentPage === page ? 'default' : 'outline'}
                            size="icon"
                            onClick={() => handlePageChange(page)}
                            data-testid={`page-${page}-btn`}
                          >
                            {page}
                          </Button>
                        );
                      } else if (page === currentPage - 2 || page === currentPage + 2) {
                        return <span key={page} className="px-2">...</span>;
                      }
                      return null;
                    })}
                    
                    <Button
                      variant="outline"
                      size="icon"
                      disabled={currentPage === totalPages}
                      onClick={() => handlePageChange(currentPage + 1)}
                      data-testid="next-page-btn"
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                )}
              </>
            ) : (
              <Card className="text-center py-16" data-testid="no-products">
                <CardContent>
                  <div className="w-16 h-16 mx-auto rounded-full bg-muted flex items-center justify-center mb-4">
                    <Search className="h-8 w-8 text-muted-foreground" />
                  </div>
                  <h3 className="font-heading text-xl font-semibold mb-2">
                    No products found
                  </h3>
                  <p className="text-muted-foreground mb-4">
                    Try adjusting your filters or search terms
                  </p>
                  <Button onClick={clearFilters} data-testid="clear-filters-empty-btn">
                    Clear Filters
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default StorePage;
