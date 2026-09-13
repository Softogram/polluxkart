import React, { useState, useEffect } from 'react';
import {
  Plus,
  Search,
  Edit,
  Trash2,
  Loader2,
  Upload,
  X,
  Image as ImageIcon,
  ExternalLink,
  RefreshCw,
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import { Card, CardContent } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Switch } from '../../components/ui/switch';
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

const AdminBrands = () => {
  const [brands, setBrands] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isMigrateDialogOpen, setIsMigrateDialogOpen] = useState(false);
  const [selectedBrand, setSelectedBrand] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isMigrating, setIsMigrating] = useState(false);
  const [uploadingLogo, setUploadingLogo] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    logo: '',
    website: '',
    is_active: true,
  });

  useEffect(() => {
    loadBrands();
  }, []);

  const loadBrands = async () => {
    setIsLoading(true);
    try {
      const data = await AdminService.getAdminBrands(true);
      setBrands(data || []);
    } catch (error) {
      toast.error('Failed to load brands');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogoUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingLogo(true);
    try {
      const result = await AdminService.uploadImage(file);
      setFormData(prev => ({ ...prev, logo: result.url }));
      toast.success('Logo uploaded successfully');
    } catch (error) {
      toast.error('Failed to upload logo');
      console.error(error);
    } finally {
      setUploadingLogo(false);
    }
  };

  const openCreateDialog = () => {
    setSelectedBrand(null);
    setFormData({
      name: '',
      description: '',
      logo: '',
      website: '',
      is_active: true,
    });
    setIsDialogOpen(true);
  };

  const openEditDialog = (brand) => {
    setSelectedBrand(brand);
    setFormData({
      name: brand.name || '',
      description: brand.description || '',
      logo: brand.logo || '',
      website: brand.website || '',
      is_active: brand.is_active !== false,
    });
    setIsDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      toast.error('Brand name is required');
      return;
    }

    setIsSubmitting(true);
    try {
      const brandData = {
        name: formData.name.trim(),
        description: formData.description || null,
        logo: formData.logo || null,
        website: formData.website || null,
        is_active: formData.is_active,
      };

      if (selectedBrand) {
        await AdminService.updateBrand(selectedBrand.id, brandData);
        toast.success('Brand updated successfully');
      } else {
        await AdminService.createBrand(brandData);
        toast.success('Brand created successfully');
      }

      setIsDialogOpen(false);
      loadBrands();
    } catch (error) {
      toast.error(error.message || 'Failed to save brand');
      console.error(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedBrand) return;

    try {
      await AdminService.deleteBrand(selectedBrand.id);
      toast.success('Brand deleted successfully');
      setIsDeleteDialogOpen(false);
      setSelectedBrand(null);
      loadBrands();
    } catch (error) {
      toast.error(error.message || 'Failed to delete brand');
      console.error(error);
    }
  };

  const handleMigrate = async () => {
    setIsMigrating(true);
    try {
      const result = await AdminService.migrateBrands();
      toast.success(`Migration complete: ${result.details?.migrated || 0} brands migrated`);
      setIsMigrateDialogOpen(false);
      loadBrands();
    } catch (error) {
      toast.error('Failed to migrate brands');
      console.error(error);
    } finally {
      setIsMigrating(false);
    }
  };

  const filteredBrands = brands.filter(b =>
    b.name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
          <h1 className="text-2xl font-bold text-gray-900">Brands</h1>
          <p className="text-gray-500">{brands.length} brands total</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setIsMigrateDialogOpen(true)}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Migrate from Products
          </Button>
          <Button onClick={openCreateDialog}>
            <Plus className="mr-2 h-4 w-4" />
            Add Brand
          </Button>
        </div>
      </div>

      {/* Search */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search brands..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Brands Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Brand</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Website</TableHead>
                <TableHead>Products</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredBrands.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                    No brands found. Click "Add Brand" to create one or "Migrate from Products" to import existing brands.
                  </TableCell>
                </TableRow>
              ) : (
                filteredBrands.map((brand) => (
                  <TableRow key={brand.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-gray-100 overflow-hidden flex items-center justify-center">
                          {brand.logo ? (
                            <img
                              src={brand.logo}
                              alt={brand.name}
                              className="w-full h-full object-contain"
                            />
                          ) : (
                            <ImageIcon className="h-5 w-5 text-gray-400" />
                          )}
                        </div>
                        <span className="font-medium">{brand.name}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-gray-500 line-clamp-1">
                        {brand.description || '-'}
                      </span>
                    </TableCell>
                    <TableCell>
                      {brand.website ? (
                        <a
                          href={brand.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-primary hover:underline flex items-center gap-1"
                        >
                          Visit <ExternalLink className="h-3 w-3" />
                        </a>
                      ) : (
                        <span className="text-sm text-gray-400">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{brand.product_count || 0}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={brand.is_active ? 'default' : 'secondary'}>
                        {brand.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button size="sm" variant="ghost" onClick={() => openEditDialog(brand)}>
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-destructive"
                          onClick={() => {
                            setSelectedBrand(brand);
                            setIsDeleteDialogOpen(true);
                          }}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{selectedBrand ? 'Edit Brand' : 'Add New Brand'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Brand Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Enter brand name"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Brand description (optional)"
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="website">Website URL</Label>
              <Input
                id="website"
                type="url"
                value={formData.website}
                onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                placeholder="https://example.com"
              />
            </div>

            {/* Logo Upload */}
            <div className="space-y-2">
              <Label>Brand Logo</Label>
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-lg border-2 border-dashed flex items-center justify-center bg-gray-50 overflow-hidden">
                  {formData.logo ? (
                    <img
                      src={formData.logo}
                      alt="Brand logo"
                      className="w-full h-full object-contain"
                    />
                  ) : (
                    <ImageIcon className="h-6 w-6 text-gray-400" />
                  )}
                </div>
                <div className="flex-1">
                  <input
                    type="file"
                    id="logo-upload"
                    accept="image/*"
                    className="hidden"
                    onChange={handleLogoUpload}
                  />
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => document.getElementById('logo-upload').click()}
                      disabled={uploadingLogo}
                    >
                      {uploadingLogo ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <>
                          <Upload className="h-4 w-4 mr-1" /> Upload
                        </>
                      )}
                    </Button>
                    {formData.logo && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => setFormData({ ...formData, logo: '' })}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Active Toggle */}
            <div className="flex items-center justify-between">
              <Label htmlFor="is_active">Active Status</Label>
              <Switch
                id="is_active"
                checked={formData.is_active}
                onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
              />
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
                ) : selectedBrand ? (
                  'Update Brand'
                ) : (
                  'Create Brand'
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
            <AlertDialogTitle>Delete Brand</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{selectedBrand?.name}"? 
              {selectedBrand?.product_count > 0 && (
                <span className="block mt-2 text-red-600">
                  Warning: This brand has {selectedBrand.product_count} products associated with it. 
                  You must reassign those products to another brand first.
                </span>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleDelete} 
              className="bg-destructive text-destructive-foreground"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Migrate Confirmation */}
      <AlertDialog open={isMigrateDialogOpen} onOpenChange={setIsMigrateDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Migrate Brands from Products</AlertDialogTitle>
            <AlertDialogDescription>
              This will scan all existing products and create brand entries for any brands that don't exist yet.
              Existing brands will be skipped.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isMigrating}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleMigrate} disabled={isMigrating}>
              {isMigrating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Migrating...
                </>
              ) : (
                'Start Migration'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default AdminBrands;
