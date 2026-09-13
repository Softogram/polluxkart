import React, { useState, useEffect } from 'react';
import {
  Search,
  Eye,
  Truck,
  Package,
  CheckCircle,
  XCircle,
  Loader2,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
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
import AdminService from '../../services/adminService';
import { formatPrice } from '../../utils/currency';
import { toast } from 'sonner';

const ORDER_STATUSES = [
  { value: 'pending', label: 'Pending', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'confirmed', label: 'Confirmed', color: 'bg-blue-100 text-blue-800' },
  { value: 'processing', label: 'Processing', color: 'bg-purple-100 text-purple-800' },
  { value: 'shipped', label: 'Shipped', color: 'bg-indigo-100 text-indigo-800' },
  { value: 'delivered', label: 'Delivered', color: 'bg-green-100 text-green-800' },
  { value: 'cancelled', label: 'Cancelled', color: 'bg-red-100 text-red-800' },
];

const AdminOrders = () => {
  const [orders, setOrders] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [isViewDialogOpen, setIsViewDialogOpen] = useState(false);
  const [isStatusDialogOpen, setIsStatusDialogOpen] = useState(false);
  const [newStatus, setNewStatus] = useState('');
  const [trackingNumber, setTrackingNumber] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);

  useEffect(() => {
    loadOrders();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, statusFilter]);

  const loadOrders = async () => {
    setIsLoading(true);
    try {
      const data = await AdminService.getAdminOrders(
        currentPage,
        20,
        statusFilter || null,
        searchQuery || null
      );
      setOrders(data.orders || []);
      setTotalPages(data.total_pages || 1);
    } catch (error) {
      toast.error('Failed to load orders');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = () => {
    setCurrentPage(1);
    loadOrders();
  };

  const openStatusDialog = (order) => {
    setSelectedOrder(order);
    setNewStatus(order.status);
    setTrackingNumber(order.tracking_number || '');
    setIsStatusDialogOpen(true);
  };

  const handleUpdateStatus = async () => {
    if (!selectedOrder || !newStatus) return;

    setIsUpdating(true);
    try {
      await AdminService.updateOrderStatus(
        selectedOrder.id,
        newStatus,
        newStatus === 'shipped' ? trackingNumber : null
      );
      toast.success('Order status updated');
      setIsStatusDialogOpen(false);
      loadOrders();
    } catch (error) {
      toast.error('Failed to update status');
      console.error(error);
    } finally {
      setIsUpdating(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusInfo = ORDER_STATUSES.find(s => s.value === status) || ORDER_STATUSES[0];
    return (
      <Badge className={statusInfo.color}>
        {statusInfo.label}
      </Badge>
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading && orders.length === 0) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Orders</h1>
        <p className="text-gray-500">Manage and track customer orders</p>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search by order number or customer..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="pl-10"
              />
            </div>
            <Select value={statusFilter} onValueChange={(value) => {
              setStatusFilter(value === 'all' ? '' : value);
              setCurrentPage(1);
            }}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                {ORDER_STATUSES.map((status) => (
                  <SelectItem key={status.value} value={status.value}>
                    {status.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button onClick={handleSearch}>Search</Button>
          </div>
        </CardContent>
      </Card>

      {/* Orders Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Order</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead>Items</TableHead>
                <TableHead>Total</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Date</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {orders.map((order) => (
                <TableRow key={order.id}>
                  <TableCell>
                    <span className="font-mono font-medium">
                      #{order.order_number}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div>
                      <p className="font-medium">{order.shipping_address?.full_name}</p>
                      <p className="text-sm text-gray-500">{order.shipping_address?.phone}</p>
                    </div>
                  </TableCell>
                  <TableCell>
                    {order.items?.length || 0} item(s)
                  </TableCell>
                  <TableCell className="font-medium">
                    {formatPrice(order.total)}
                  </TableCell>
                  <TableCell>{getStatusBadge(order.status)}</TableCell>
                  <TableCell className="text-sm text-gray-500">
                    {formatDate(order.created_at)}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setSelectedOrder(order);
                          setIsViewDialogOpen(true);
                        }}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => openStatusDialog(order)}
                      >
                        Update Status
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {orders.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No orders found
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-6">
          <Button
            variant="outline"
            size="sm"
            disabled={currentPage === 1}
            onClick={() => setCurrentPage(p => p - 1)}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-sm text-gray-500">
            Page {currentPage} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={currentPage === totalPages}
            onClick={() => setCurrentPage(p => p + 1)}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* View Order Dialog */}
      <Dialog open={isViewDialogOpen} onOpenChange={setIsViewDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Order #{selectedOrder?.order_number}</DialogTitle>
          </DialogHeader>
          {selectedOrder && (
            <div className="space-y-4">
              {/* Order Status */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm text-gray-500">Status</p>
                  {getStatusBadge(selectedOrder.status)}
                </div>
                <div>
                  <p className="text-sm text-gray-500">Payment</p>
                  <Badge variant="outline">{selectedOrder.payment_method?.toUpperCase()}</Badge>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total</p>
                  <p className="font-bold">{formatPrice(selectedOrder.total)}</p>
                </div>
              </div>

              {/* Shipping Address */}
              <div>
                <h4 className="font-medium mb-2">Shipping Address</h4>
                <div className="p-4 bg-gray-50 rounded-lg text-sm">
                  <p className="font-medium">{selectedOrder.shipping_address?.full_name}</p>
                  <p>{selectedOrder.shipping_address?.phone}</p>
                  <p>{selectedOrder.shipping_address?.address_line1}</p>
                  {selectedOrder.shipping_address?.address_line2 && (
                    <p>{selectedOrder.shipping_address.address_line2}</p>
                  )}
                  <p>
                    {selectedOrder.shipping_address?.city}, {selectedOrder.shipping_address?.state} - {selectedOrder.shipping_address?.pincode}
                  </p>
                </div>
              </div>

              {/* Order Items */}
              <div>
                <h4 className="font-medium mb-2">Items</h4>
                <div className="space-y-2">
                  {selectedOrder.items?.map((item, index) => (
                    <div key={index} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
                      <div className="w-12 h-12 bg-gray-200 rounded overflow-hidden">
                        {item.image && (
                          <img src={item.image} alt={item.product_name} className="w-full h-full object-cover" />
                        )}
                      </div>
                      <div className="flex-1">
                        <p className="font-medium">{item.product_name}</p>
                        <p className="text-sm text-gray-500">Qty: {item.quantity}</p>
                      </div>
                      <p className="font-medium">{formatPrice(item.price * item.quantity)}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Tracking */}
              {selectedOrder.tracking_number && (
                <div>
                  <h4 className="font-medium mb-2">Tracking</h4>
                  <p className="font-mono bg-gray-50 p-3 rounded-lg">
                    {selectedOrder.tracking_number}
                  </p>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Update Status Dialog */}
      <Dialog open={isStatusDialogOpen} onOpenChange={setIsStatusDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Update Order Status</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Status</Label>
              <Select value={newStatus} onValueChange={setNewStatus}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ORDER_STATUSES.map((status) => (
                    <SelectItem key={status.value} value={status.value}>
                      {status.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            {newStatus === 'shipped' && (
              <div className="space-y-2">
                <Label>Tracking Number</Label>
                <Input
                  value={trackingNumber}
                  onChange={(e) => setTrackingNumber(e.target.value)}
                  placeholder="Enter tracking number"
                />
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsStatusDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdateStatus} disabled={isUpdating}>
              {isUpdating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Updating...
                </>
              ) : (
                'Update Status'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminOrders;
