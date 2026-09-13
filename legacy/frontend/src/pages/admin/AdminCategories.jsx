import React, { useState, useEffect } from 'react';
import {
  Plus,
  Edit,
  Trash2,
  Loader2,
  Tag,
  Upload,
  X,
  Image as ImageIcon,
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import { Card, CardContent } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../../components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/ui/table';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../../components/ui/alert-dialog';
import AdminService from '../../services/adminService';
import { toast } from 'sonner';

const AdminCategories = () => {
  const [categories, setCategories] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    image: '',
    is_active: true,
  });

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    setIsLoading(true);
    try {
      const data = await AdminService.getAdminCategories();
      setCategories(data || []);
    } catch (error) {
      toast.error('Failed to load categories');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploadingImage(true);
    try {
      const result = await AdminService.uploadImage(file);
      setFormData(prev => ({ ...prev, image: result.url }));
      toast.success('Image uploaded successfully');
    } catch (error) {
      toast.error('Failed to upload image');
      console.error(error);
    } finally {
      setUploadingImage(false);
    }
  };

  const removeImage = () => {
    setFormData(prev => ({ ...prev, image: '' }));
  };

  const openCreateDialog = () => {
    setSelectedCategory(null);
    setFormData({
      name: '',
      description: '',
      image: '',
      is_active: true,
    });
    setIsDialogOpen(true);
  };

  const openEditDialog = (category) => {
    setSelectedCategory(category);
    setFormData({
      name: category.name || '',
      description: category.description || '',
      image: category.image || '',
      is_active: category.is_active !== false,
    });
    setIsDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name) {
      toast.error('Category name is required');
      return;
    }

    setIsSubmitting(true);
    try {
      const categoryData = {
        name: formData.name,
        description: formData.description || null,
        image: formData.image || null,
        is_active: formData.is_active,
      };

      if (selectedCategory) {
        await AdminService.updateCategory(selectedCategory.id, categoryData);
        toast.success('Category updated successfully');
      } else {
        await AdminService.createCategory(categoryData);
        toast.success('Category created successfully');
      }

      setIsDialogOpen(false);
      loadCategories();
    } catch (error) {
      toast.error(error.message || 'Failed to save category');
      console.error(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedCategory) return;

    try {
      await AdminService.deleteCategory(selectedCategory.id);
      toast.success('Category deleted successfully');
      setIsDeleteDialogOpen(false);
      setSelectedCategory(null);
      loadCategories();
    } catch (error) {
      toast.error(error.message || 'Failed to delete category');
      console.error(error);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Categories</h1>
          <p className="text-gray-500">{categories.length} categories total</p>
        </div>
        <Button onClick={openCreateDialog}>
          <Plus className="mr-2 h-4 w-4" />
          Add Category
        </Button>
      </div>

      {/* Categories Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Category</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Products</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {categories.map((category) => (
                <TableRow key={category.id}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-gray-100 overflow-hidden flex items-center justify-center">
                        {category.image ? (
                          <img
                            src={category.image}
                            alt={category.name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <Tag className="h-5 w-5 text-primary" />
                        )}
                      </div>
                      <span className="font-medium">{category.name}</span>
                    </div>
                  </TableCell>
                  <TableCell className="max-w-xs truncate text-gray-500">
                    {category.description || '-'}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{category.product_count || 0}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={category.is_active !== false ? 'default' : 'secondary'}>
                      {category.is_active !== false ? 'Active' : 'Inactive'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button size="sm" variant="ghost" onClick={() => openEditDialog(category)}>
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-destructive"
                        onClick={() => {
                          setSelectedCategory(category);
                          setIsDeleteDialogOpen(true);
                        }}
                        disabled={category.product_count > 0}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {categories.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No categories found. Create one to get started.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{selectedCategory ? 'Edit Category' : 'Add New Category'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Category name"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Category description"
                rows={3}
              />
            </div>

            {/* Image Upload */}
            <div className="space-y-2">
              <Label>Category Image</Label>
              {formData.image ? (
                <div className="relative w-32 h-32">
                  <img
                    src={formData.image}
                    alt="Category"
                    className="w-full h-full object-cover rounded-lg border"
                  />
                  <button
                    type="button"
                    onClick={removeImage}
                    className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ) : (
                <div className="border-2 border-dashed rounded-lg p-4">
                  <input
                    type="file"
                    id="category-image-upload"
                    accept="image/*"
                    className="hidden"
                    onChange={handleImageUpload}
                  />
                  <label
                    htmlFor="category-image-upload"
                    className="flex flex-col items-center justify-center cursor-pointer py-4"
                  >
                    {uploadingImage ? (
                      <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                    ) : (
                      <Upload className="h-8 w-8 text-gray-400" />
                    )}
                    <span className="mt-2 text-sm text-gray-500">
                      {uploadingImage ? 'Uploading...' : 'Click to upload image'}
                    </span>
                  </label>
                </div>
              )}
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : selectedCategory ? (
                  'Update Category'
                ) : (
                  'Create Category'
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Category</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{selectedCategory?.name}"? This action cannot be undone.
              {selectedCategory?.product_count > 0 && (
                <span className="block mt-2 text-red-500 font-medium">
                  This category has {selectedCategory.product_count} products and cannot be deleted.
                </span>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground"
              disabled={selectedCategory?.product_count > 0}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default AdminCategories;
