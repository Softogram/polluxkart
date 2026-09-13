import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Package,
  Truck,
  CheckCircle2,
  Clock,
  ChevronRight,
  ShoppingBag,
  MapPin,
  CreditCard,
  RefreshCw,
  ShoppingCart,
  Loader2,
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Separator } from '../components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '../components/ui/breadcrumb';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import OrderService from '../services/orderService';
import { formatPrice } from '../utils/currency';
import { toast } from 'sonner';

const OrdersPage = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { addToCart } = useCart();
  const [orders, setOrders] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadOrders = async () => {
      if (!isAuthenticated) {
        setIsLoading(false);
        return;
      }
      
      try {
        const response = await OrderService.getOrders();
        // Transform API response to match expected format
        const transformedOrders = (response.orders || []).map(order => ({
          id: order.id,
          orderNumber: order.order_number,
          date: order.created_at,
          status: order.status,
          paymentStatus: order.payment_status,
          paymentMethod: order.payment_method,
          items: order.items.map(item => ({
            id: item.product_id,
            name: item.name,
            price: item.price,
            quantity: item.quantity,
            image: item.image,
            total: item.total,
          })),
          shipping: order.shipping_fee,
          tax: order.tax,
          subtotal: order.subtotal,
          total: order.total,
          address: order.shipping_address ? {
            name: order.shipping_address.full_name,
            street: order.shipping_address.address_line1,
            city: order.shipping_address.city,
            state: order.shipping_address.state,
            pincode: order.shipping_address.pincode,
          } : null,
        }));
        setOrders(transformedOrders);
      } catch (error) {
        console.error('Failed to load orders:', error);
        toast.error('Failed to load orders');
      } finally {
        setIsLoading(false);
      }
    };

    loadOrders();
  }, [isAuthenticated]);

  const handleReorder = (order) => {
    // Add all items from the order to cart
    order.items.forEach(item => {
      addToCart({
        id: item.id,
        name: item.name,
        price: item.price,
        image: item.image,
        category: item.category || 'General',
        rating: item.rating || 4.5,
        reviews: item.reviews || 100,
        inStock: true,
      }, item.quantity);
    });
    toast.success(`${order.items.length} items added to cart!`);
    navigate('/cart');
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'confirmed':
        return 'bg-success/10 text-success border-success/20';
      case 'processing':
        return 'bg-warning/10 text-warning border-warning/20';
      case 'shipped':
        return 'bg-primary/10 text-primary border-primary/20';
      case 'delivered':
        return 'bg-success/10 text-success border-success/20';
      default:
        return 'bg-muted text-muted-foreground';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'confirmed':
        return <CheckCircle2 className="h-4 w-4" />;
      case 'processing':
        return <Clock className="h-4 w-4" />;
      case 'shipped':
        return <Truck className="h-4 w-4" />;
      case 'delivered':
        return <Package className="h-4 w-4" />;
      default:
        return <Package className="h-4 w-4" />;
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Date not available';
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return 'Date not available';
      return date.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    } catch {
      return 'Date not available';
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-24 h-24 rounded-full bg-muted flex items-center justify-center mb-6">
              <Package className="h-12 w-12 text-muted-foreground" />
            </div>
            <h2 className="font-heading text-2xl font-bold text-foreground mb-2">
              Please login to view orders
            </h2>
            <p className="text-muted-foreground mb-6">
              You need to be logged in to see your order history.
            </p>
            <Button onClick={() => navigate('/auth')}>Login / Sign Up</Button>
          </div>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
            <p className="text-muted-foreground">Loading your orders...</p>
          </div>
        </div>
      </div>
    );
  }

  if (orders.length === 0) {
    return (
      <div className="min-h-screen bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Breadcrumb className="mb-6">
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink asChild>
                  <Link to="/">Home</Link>
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbPage>Orders</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>

          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-24 h-24 rounded-full bg-muted flex items-center justify-center mb-6">
              <ShoppingBag className="h-12 w-12 text-muted-foreground" />
            </div>
            <h2 className="font-heading text-2xl font-bold text-foreground mb-2">
              No orders yet
            </h2>
            <p className="text-muted-foreground mb-6">
              You haven't placed any orders yet. Start shopping!
            </p>
            <Button onClick={() => navigate('/store')}>
              Start Shopping
              <ChevronRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    );
  }

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
              <BreadcrumbPage>Orders</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>

        {/* Page Header */}
        <div className="mb-8">
          <h1 className="font-heading text-3xl font-bold text-foreground">My Orders</h1>
          <p className="text-muted-foreground mt-1">
            Track and manage your orders
          </p>
        </div>

        {/* Orders Tabs */}
        <Tabs defaultValue="all" className="space-y-6">
          <TabsList className="bg-muted/50">
            <TabsTrigger value="all">All Orders</TabsTrigger>
            <TabsTrigger value="processing">Processing</TabsTrigger>
            <TabsTrigger value="delivered">Delivered</TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="space-y-4">
            {orders.map((order) => (
              <OrderCard
                key={order.id}
                order={order}
                getStatusColor={getStatusColor}
                getStatusIcon={getStatusIcon}
                formatDate={formatDate}
                onReorder={handleReorder}
              />
            ))}
          </TabsContent>

          <TabsContent value="processing" className="space-y-4">
            {orders
              .filter((o) => ['confirmed', 'processing', 'shipped'].includes(o.status))
              .map((order) => (
                <OrderCard
                  key={order.id}
                  order={order}
                  getStatusColor={getStatusColor}
                  getStatusIcon={getStatusIcon}
                  formatDate={formatDate}
                  onReorder={handleReorder}
                />
              ))}
          </TabsContent>

          <TabsContent value="delivered" className="space-y-4">
            {orders
              .filter((o) => o.status === 'delivered')
              .map((order) => (
                <OrderCard
                  key={order.id}
                  order={order}
                  getStatusColor={getStatusColor}
                  getStatusIcon={getStatusIcon}
                  formatDate={formatDate}
                  onReorder={handleReorder}
                />
              ))}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

const OrderCard = ({ order, getStatusColor, getStatusIcon, formatDate, onReorder }) => {
  return (
    <Card>
      <CardHeader className="pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="space-y-1">
            <CardTitle className="font-heading text-lg">Order #{order.orderNumber}</CardTitle>
            <p className="text-sm text-muted-foreground">
              Placed on {formatDate(order.date)}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge
              variant="outline"
              className={`${getStatusColor(order.status)} capitalize w-fit`}
            >
              {getStatusIcon(order.status)}
              <span className="ml-1">{order.status}</span>
            </Badge>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onReorder(order)}
              className="gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Reorder
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Order Items */}
        <div className="space-y-3">
          {order.items.map((item) => (
            <div key={item.id} className="flex gap-4">
              <Link to={`/product/${item.id}`} className="shrink-0">
                <div className="w-16 h-16 rounded-lg overflow-hidden bg-muted">
                  <img
                    src={item.image}
                    alt={item.name}
                    className="w-full h-full object-cover"
                  />
                </div>
              </Link>
              <div className="flex-1 min-w-0">
                <Link
                  to={`/product/${item.id}`}
                  className="font-medium text-foreground hover:text-primary line-clamp-1"
                >
                  {item.name}
                </Link>
                <p className="text-sm text-muted-foreground">Qty: {item.quantity}</p>
                <p className="text-sm font-medium text-foreground">
                  {formatPrice(item.price * item.quantity)}
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="shrink-0"
                onClick={() => {
                  onReorder({ items: [item] });
                }}
              >
                <ShoppingCart className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>

        <Separator />

        {/* Order Details */}
        <div className="grid sm:grid-cols-3 gap-4">
          {/* Delivery Address */}
          {order.address && (
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-sm font-medium text-foreground">
                <MapPin className="h-4 w-4 text-primary" />
                Delivery Address
              </div>
              <p className="text-sm text-muted-foreground">
                {order.address.street}, {order.address.city}, {order.address.state} -{' '}
                {order.address.pincode}
              </p>
            </div>
          )}

          {/* Payment Method */}
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-sm font-medium text-foreground">
              <CreditCard className="h-4 w-4 text-primary" />
              Payment Method
            </div>
            <p className="text-sm text-muted-foreground capitalize">
              {order.paymentMethod === 'razorpay' ? 'Razorpay' : order.paymentMethod}
            </p>
          </div>

          {/* Total */}
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-sm font-medium text-foreground">
              <Package className="h-4 w-4 text-primary" />
              Order Total
            </div>
            <p className="text-lg font-bold text-primary">{formatPrice(order.total)}</p>
          </div>
        </div>

        {/* Order Tracking Timeline */}
        <div className="pt-4">
          <div className="flex items-center justify-between relative">
            <div className="absolute left-0 right-0 top-1/2 h-1 bg-muted -translate-y-1/2" />
            <div 
              className="absolute left-0 top-1/2 h-1 bg-primary -translate-y-1/2 transition-all duration-300" 
              style={{ 
                width: order.status === 'pending' ? '0%' 
                     : order.status === 'confirmed' ? '25%' 
                     : order.status === 'processing' ? '50%' 
                     : order.status === 'shipped' ? '75%' 
                     : order.status === 'delivered' ? '100%' 
                     : '0%' 
              }} 
            />
            
            {['pending', 'confirmed', 'processing', 'shipped', 'delivered'].map((step, index) => {
              const statusOrder = ['pending', 'confirmed', 'processing', 'shipped', 'delivered'];
              const currentStatusIndex = statusOrder.indexOf(order.status);
              const isCompleted = currentStatusIndex >= index;
              const isCurrent = order.status === step;
              
              return (
                <div key={step} className="relative flex flex-col items-center z-10">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${
                      isCompleted
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted text-muted-foreground'
                    } ${isCurrent ? 'ring-2 ring-primary ring-offset-2' : ''}`}
                  >
                    {isCompleted ? (
                      <CheckCircle2 className="h-4 w-4" />
                    ) : (
                      <span className="text-xs">{index + 1}</span>
                    )}
                  </div>
                  <span className={`text-xs mt-2 capitalize hidden sm:block ${isCurrent ? 'text-primary font-medium' : 'text-muted-foreground'}`}>
                    {step === 'pending' ? 'Order Placed' : step}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default OrdersPage;
