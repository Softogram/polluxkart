import React, { useState, useEffect } from 'react';
import {
  Plus,
  Edit,
  Trash2,
  Loader2,
  Percent,
  Calendar,
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/select';
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
import { formatPrice } from '../../utils/currency';
import { toast } from 'sonner';

const AdminPromotions = () => {
  const [promotions, setPromotions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedPromotion, setSelectedPromotion] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const [formData, setFormData] = useState({
    code: '',
    description: '',
    discount_type: 'percentage',
    discount_value: '',
    min_order_amount: '',
    max_discount: '',
    usage_limit: '',
    per_user_limit: '1',
    start_date: '',
    end_date: '',
    status: 'active',
  });

  useEffect(() => {
    loadPromotions();
  }, []);

  const loadPromotions = async () => {
    setIsLoading(true);
    try {
      const data = await AdminService.getPromotions();
      setPromotions(data || []);
    } catch (error) {
      toast.error('Failed to load promotions');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const openCreateDialog = () => {
    setSelectedPromotion(null);
    setFormData({
      code: '',
      description: '',
      discount_type: 'percentage',
      discount_value: '',
      min_order_amount: '',
      max_discount: '',
      usage_limit: '',
      per_user_limit: '1',
      start_date: '',
      end_date: '',
      status: 'active',
    });
    setIsDialogOpen(true);
  };

  const openEditDialog = (promo) => {
    setSelectedPromotion(promo);
    setFormData({
      code: promo.code || '',
      description: promo.description || '',
      discount_type: promo.discount_type || 'percentage',
      discount_value: promo.discount_value?.toString() || '',
      min_order_amount: promo.min_order_amount?.toString() || '',
      max_discount: promo.max_discount?.toString() || '',
      usage_limit: promo.usage_limit?.toString() || '',
      per_user_limit: promo.per_user_limit?.toString() || '1',
      start_date: promo.start_date ? promo.start_date.split('T')[0] : '',
      end_date: promo.end_date ? promo.end_date.split('T')[0] : '',
      status: promo.status || 'active',
    });
    setIsDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.code || !formData.discount_value) {
      toast.error('Please fill in required fields');
      return;
    }

    setIsSubmitting(true);
    try {
      const promoData = {
        code: formData.code.toUpperCase(),
        description: formData.description || null,
        discount_type: formData.discount_type,
        discount_value: parseFloat(formData.discount_value),
        min_order_amount: formData.min_order_amount ? parseFloat(formData.min_order_amount) : null,
        max_discount: formData.max_discount ? parseFloat(formData.max_discount) : null,
        usage_limit: formData.usage_limit ? parseInt(formData.usage_limit) : null,
        per_user_limit: parseInt(formData.per_user_limit) || 1,
        start_date: formData.start_date ? new Date(formData.start_date).toISOString() : null,
        end_date: formData.end_date ? new Date(formData.end_date).toISOString() : null,
      };

      if (selectedPromotion) {
        promoData.status = formData.status;
        await AdminService.updatePromotion(selectedPromotion.id, promoData);
        toast.success('Promotion updated successfully');
      } else {
        await AdminService.createPromotion(promoData);
        toast.success('Promotion created successfully');
      }

      setIsDialogOpen(false);
      loadPromotions();
    } catch (error) {
      toast.error(error.message || 'Failed to save promotion');
      console.error(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedPromotion) return;

    try {
      await AdminService.deletePromotion(selectedPromotion.id);
      toast.success('Promotion deleted successfully');
      setIsDeleteDialogOpen(false);
      setSelectedPromotion(null);
      loadPromotions();
    } catch (error) {
      toast.error('Failed to delete promotion');
      console.error(error);
    }
  };

  const getStatusBadge = (status) => {
    const colors = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-gray-100 text-gray-800',
      expired: 'bg-red-100 text-red-800',
    };
    return <Badge className={colors[status] || colors.inactive}>{status}</Badge>;
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
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
          <h1 className="text-2xl font-bold text-gray-900">Promotions</h1>
          <p className="text-gray-500">Manage discount codes and offers</p>
        </div>
        <Button onClick={openCreateDialog}>
          <Plus className="mr-2 h-4 w-4" />
          Add Promotion
        </Button>
      </div>

      {/* Promotions Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Code</TableHead>
                <TableHead>Discount</TableHead>
                <TableHead>Min Order</TableHead>
                <TableHead>Usage</TableHead>
                <TableHead>Validity</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {promotions.map((promo) => (
                <TableRow key={promo.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                        <Percent className="h-4 w-4 text-primary" />
                      </div>
                      <span className="font-mono font-medium">{promo.code}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    {promo.discount_type === 'percentage'
                      ? `${promo.discount_value}%`
                      : formatPrice(promo.discount_value)}
                    {promo.max_discount && (
                      <span className="text-xs text-gray-500 block">
                        Max: {formatPrice(promo.max_discount)}
                      </span>
                    )}
                  </TableCell>
                  <TableCell>
                    {promo.min_order_amount ? formatPrice(promo.min_order_amount) : '-'}
                  </TableCell>
                  <TableCell>
                    {promo.times_used || 0}
                    {promo.usage_limit && ` / ${promo.usage_limit}`}
                  </TableCell>
                  <TableCell className="text-sm">
                    <div className="flex items-center gap-1 text-gray-500">
                      <Calendar className="h-3 w-3" />
                      {formatDate(promo.start_date)} - {formatDate(promo.end_date)}
                    </div>
                  </TableCell>
                  <TableCell>{getStatusBadge(promo.status)}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button size="sm" variant="ghost" onClick={() => openEditDialog(promo)}>
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-destructive"
                        onClick={() => {
                          setSelectedPromotion(promo);
                          setIsDeleteDialogOpen(true);
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {promotions.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No promotions found. Create one to offer discounts.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{selectedPromotion ? 'Edit Promotion' : 'Add New Promotion'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="code">Code *</Label>
                <Input
                  id="code"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                  placeholder="SAVE20"
                  required
                  disabled={!!selectedPromotion}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="discount_type">Discount Type</Label>
                <Select
                  value={formData.discount_type}
                  onValueChange={(value) => setFormData({ ...formData, discount_type: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="percentage">Percentage (%)</SelectItem>
                    <SelectItem value="fixed">Fixed Amount (₹)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Save 20% on your order"
                rows={2}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="discount_value">Discount Value *</Label>
                <Input
                  id="discount_value"
                  type="number"
                  value={formData.discount_value}
                  onChange={(e) => setFormData({ ...formData, discount_value: e.target.value })}
                  placeholder={formData.discount_type === 'percentage' ? '20' : '100'}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="max_discount">Max Discount (₹)</Label>
                <Input
                  id="max_discount"
                  type="number"
                  value={formData.max_discount}
                  onChange={(e) => setFormData({ ...formData, max_discount: e.target.value })}
                  placeholder="500"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="min_order_amount">Min Order Amount (₹)</Label>
                <Input
                  id="min_order_amount"
                  type="number"
                  value={formData.min_order_amount}
                  onChange={(e) => setFormData({ ...formData, min_order_amount: e.target.value })}
                  placeholder="1000"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="usage_limit">Usage Limit</Label>
                <Input
                  id="usage_limit"
                  type="number"
                  value={formData.usage_limit}
                  onChange={(e) => setFormData({ ...formData, usage_limit: e.target.value })}
                  placeholder="100"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="start_date">Start Date</Label>
                <Input
                  id="start_date"
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="end_date">End Date</Label>
                <Input
                  id="end_date"
                  type="date"
                  value={formData.end_date}
                  onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                />
              </div>
            </div>

            {selectedPromotion && (
              <div className="space-y-2">
                <Label htmlFor="status">Status</Label>
                <Select
                  value={formData.status}
                  onValueChange={(value) => setFormData({ ...formData, status: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                    <SelectItem value="expired">Expired</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}

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
                ) : selectedPromotion ? (
                  'Update Promotion'
                ) : (
                  'Create Promotion'
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
            <AlertDialogTitle>Delete Promotion</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete promotion "{selectedPromotion?.code}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default AdminPromotions;
