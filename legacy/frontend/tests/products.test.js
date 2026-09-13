import { products, categories, getProductById, getProductsByCategory, searchProducts } from '../src/data/products';

describe('Products Data', () => {
  describe('products array', () => {
    test('contains products', () => {
      expect(products.length).toBeGreaterThan(0);
    });

    test('all products have required fields', () => {
      products.forEach(product => {
        expect(product).toHaveProperty('id');
        expect(product).toHaveProperty('name');
        expect(product).toHaveProperty('price');
        expect(product).toHaveProperty('category');
        expect(product).toHaveProperty('image');
        expect(product).toHaveProperty('inStock');
      });
    });

    test('contains out of stock products', () => {
      const outOfStock = products.filter(p => p.inStock === false);
      expect(outOfStock.length).toBeGreaterThan(0);
    });
  });

  describe('categories', () => {
    test('contains all main categories', () => {
      const categoryIds = categories.map(c => c.id);
      expect(categoryIds).toContain('electronics');
      expect(categoryIds).toContain('fashion');
      expect(categoryIds).toContain('home');
    });

    test('each category has subcategories', () => {
      categories.forEach(category => {
        expect(category.subcategories).toBeDefined();
        expect(category.subcategories.length).toBeGreaterThan(0);
      });
    });
  });

  describe('getProductById', () => {
    test('returns product for valid id', () => {
      const product = getProductById(1);
      expect(product).toBeDefined();
      expect(product.id).toBe(1);
    });

    test('returns undefined for invalid id', () => {
      const product = getProductById(9999);
      expect(product).toBeUndefined();
    });
  });

  describe('getProductsByCategory', () => {
    test('returns products for valid category', () => {
      const electronics = getProductsByCategory('electronics');
      expect(electronics.length).toBeGreaterThan(0);
      electronics.forEach(p => {
        expect(p.category).toBe('electronics');
      });
    });

    test('returns all products for "all" category', () => {
      const all = getProductsByCategory('all');
      expect(all.length).toBe(products.length);
    });
  });

  describe('searchProducts', () => {
    test('finds products by name', () => {
      const results = searchProducts('headphones');
      expect(results.length).toBeGreaterThan(0);
    });

    test('returns empty for non-matching query', () => {
      const results = searchProducts('xyznonexistent123');
      expect(results.length).toBe(0);
    });

    test('search is case insensitive', () => {
      const lower = searchProducts('watch');
      const upper = searchProducts('WATCH');
      expect(lower.length).toBe(upper.length);
    });
  });
});
