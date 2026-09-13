import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  CreditCard,
  Truck,
  MapPin,
  ShieldCheck,
  Check,
  Plus,
  ChevronRight,
  Loader2,
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';
import { Separator } from '../components/ui/separator';
import { Textarea } from '../components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../components/ui/dialog';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '../components/ui/breadcrumb';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '../components/ui/accordion';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import OrderService from '../services/orderService';
import PaymentService from '../services/paymentService';
import CartService from '../services/cartService';
import { formatPrice } from '../utils/currency';
import { toast } from 'sonner';

const CheckoutPage = () => {
  const navigate = useNavigate();
  const { cartItems, cartTotal, clearCart } = useCart();
  const { user, isAuthenticated } = useAuth();
  
  const [selectedAddress, setSelectedAddress] = useState('address1');
  const [paymentMethod, setPaymentMethod] = useState('online');
  const [isProcessing, setIsProcessing] = useState(false);
  const [razorpayLoaded, setRazorpayLoaded] = useState(false);
  const [newAddress, setNewAddress] = useState({
    name: '',
    phone: '',
    street: '',
    city: '',
    state: '',
    pincode: '',
  });

  // Load Razorpay script on mount
  useEffect(() => {
    const loadScript = async () => {
      const loaded = await PaymentService.loadRazorpayScript();
      setRazorpayLoaded(loaded);
    };
    loadScript();
  }, []);

  // Mock saved addresses
  const savedAddresses = [
    {
      id: 'address1',
      name: user?.name || 'John Doe',
      phone: '+91 98765 43210',
      street: '123 Main Street, Apt 4B',
      city: 'Mumbai',
      state: 'Maharashtra',
      pincode: '400001',
      isDefault: true,
    },
    {
      id: 'address2',
      name: user?.name || 'John Doe',
      phone: '+91 98765 43211',
      street: '456 Oak Avenue',
      city: 'Bangalore',
      state: 'Karnataka',
      pincode: '560001',
      isDefault: false,
    },
  ];

  // Only 2 payment methods: Pay Online and Cash on Delivery
  const paymentMethods = [
    {
      id: 'online',
      name: 'Pay Online',
      description: 'Pay securely via Razorpay (Cards, UPI, Net Banking)',
      icon: CreditCard,
    },
    {
      id: 'cod',
      name: 'Cash on Delivery',
      description: 'Pay when you receive your order',
      icon: Truck,
    },
  ];

  const shipping = cartTotal > 500 ? 0 : 49;
  const tax = cartTotal * 0.18; // 18% GST
  const finalTotal = cartTotal + shipping + tax;

  // Sync cart to backend before placing order
  const syncCartToBackend = async () => {
    if (!isAuthenticated || cartItems.length === 0) return;
    
    try {
      // Clear backend cart first
      await CartService.clearCart();
      
      // Add all items from local cart to backend
      for (const item of cartItems) {
        await CartService.addToCart(item.id, item.quantity);
      }
    } catch (error) {
      console.error('Failed to sync cart:', error);
      throw new Error('Failed to sync your cart. Please try again.');
    }
  };

  const handlePlaceOrder = async () => {
    if (!isAuthenticated) {
      toast.error('Please login to place an order');
      navigate('/auth');
      return;
    }

    if (cartItems.length === 0) {
      toast.error('Your cart is empty');
      return;
    }

    setIsProcessing(true);

    try {
      // Ensure cart is synced to backend before creating order
      await syncCartToBackend();
      
      const selectedAddressData = savedAddresses.find((a) => a.id === selectedAddress);
      
      // Create order in backend
      const orderData = {
        shipping_address: {
          full_name: selectedAddressData.name,
          phone: selectedAddressData.phone,
          address_line1: selectedAddressData.street,
          address_line2: '',
          city: selectedAddressData.city,
          state: selectedAddressData.state,
          pincode: selectedAddressData.pincode,
          country: 'India',
          is_default: selectedAddressData.isDefault || false,
        },
        payment_method: paymentMethod === 'online' ? 'razorpay' : 'cod',
      };

      const order = await OrderService.createOrder(orderData);

      if (paymentMethod === 'online') {
        // Initiate Razorpay payment
        await initiateRazorpayPayment(order);
      } else {
        // COD - Order is already created, just show success
        clearCart();
        toast.success('Order placed successfully! Pay on delivery.');
        navigate('/orders');
      }
    } catch (error) {
      console.error('Order error:', error);
      toast.error(error.message || 'Failed to place order. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const initiateRazorpayPayment = async (order) => {
    if (!razorpayLoaded) {
      toast.error('Payment gateway is loading. Please try again.');
      return;
    }

    try {
      // Create Razorpay order
      const razorpayOrder = await PaymentService.createRazorpayOrder(order.id);
      
      // Check if Razorpay is properly configured
      if (!razorpayOrder.key_id || razorpayOrder.key_id === 'rzp_test_mock') {
        toast.error('Payment gateway not configured. Please use Cash on Delivery.');
        return;
      }

      // Open Razorpay checkout
      const options = {
        key: razorpayOrder.key_id,
        amount: razorpayOrder.amount,
        currency: razorpayOrder.currency || 'INR',
        name: 'PolluxKart',
        description: `Order #${order.order_number}`,
        order_id: razorpayOrder.razorpay_order_id,
        prefill: {
          name: user?.name || '',
          email: user?.email || '',
          contact: user?.phone || '',
        },
        theme: {
          color: '#14b8a6', // Teal color matching our theme
        },
        handler: async function (response) {
          // Payment successful - verify on backend
          try {
            await PaymentService.verifyRazorpayPayment({
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
              order_id: order.id,
            });

            clearCart();
            toast.success('Payment successful! Order confirmed.');
            navigate('/orders');
          } catch (verifyError) {
            console.error('Payment verification error:', verifyError);
            toast.error('Payment verification failed. Please contact support.');
          }
        },
        modal: {
          ondismiss: () => {
            toast.error('Payment cancelled');
            setIsProcessing(false);
          },
        },
      };

      // Open Razorpay checkout modal
      const rzp = new window.Razorpay(options);
      rzp.on('payment.failed', function (response) {
        console.error('Payment failed:', response.error);
        toast.error(response.error.description || 'Payment failed. Please try again.');
        setIsProcessing(false);
      });
      rzp.open();
    } catch (error) {
      console.error('Payment error:', error);
      toast.error(error.message || 'Failed to initiate payment. Please try again.');
      setIsProcessing(false);
    }
  };

  if (cartItems.length === 0) {
    return (
      <div className="min-h-screen bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col items-center justify-center py-20">
            <h2 className="font-heading text-2xl font-bold text-foreground mb-2">
              No items to checkout
            </h2>
            <p className="text-muted-foreground mb-6">
              Add some products to your cart first.
            </p>
            <Button onClick={() => navigate('/store')}>
              Continue Shopping
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
              <BreadcrumbLink asChild>
                <Link to="/cart">Cart</Link>
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage>Checkout</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>

        {/* Page Header */}
        <div className="mb-8">
          <h1 className="font-heading text-3xl font-bold text-foreground">Checkout</h1>
          <p className="text-muted-foreground mt-1">Complete your order</p>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Left Column - Forms */}
          <div className="lg:col-span-2 space-y-6">
            {/* Delivery Address */}
            <Card>
              <CardHeader>
                <CardTitle className="font-heading flex items-center gap-2">
                  <MapPin className="h-5 w-5 text-primary" />
                  Delivery Address
                </CardTitle>
              </CardHeader>
              <CardContent>
                <RadioGroup
                  value={selectedAddress}
                  onValueChange={setSelectedAddress}
                  className="space-y-4"
                >
                  {savedAddresses.map((address) => (
                    <div
                      key={address.id}
                      className={`relative flex items-start gap-4 p-4 rounded-lg border-2 transition-colors cursor-pointer ${
                        selectedAddress === address.id
                          ? 'border-primary bg-primary/5'
                          : 'border-border hover:border-primary/50'
                      }`}
                    >
                      <RadioGroupItem value={address.id} id={address.id} className="mt-1" />
                      <Label htmlFor={address.id} className="flex-1 cursor-pointer">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-foreground">{address.name}</span>
                          {address.isDefault && (
                            <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded">
                              Default
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground">{address.phone}</p>
                        <p className="text-sm text-muted-foreground">
                          {address.street}, {address.city}, {address.state} - {address.pincode}
                        </p>
                      </Label>
                      {selectedAddress === address.id && (
                        <Check className="h-5 w-5 text-primary" />
                      )}
                    </div>
                  ))}
                </RadioGroup>

                {/* Add New Address Dialog */}
                <Dialog>
                  <DialogTrigger asChild>
                    <Button variant="outline" className="w-full mt-4">
                      <Plus className="mr-2 h-4 w-4" />
                      Add New Address
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-md">
                    <DialogHeader>
                      <DialogTitle>Add New Address</DialogTitle>
                      <DialogDescription>
                        Enter your delivery address details.
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="name">Full Name</Label>
                          <Input
                            id="name"
                            placeholder="John Doe"
                            value={newAddress.name}
                            onChange={(e) =>
                              setNewAddress({ ...newAddress, name: e.target.value })
                            }
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="phone">Phone Number</Label>
                          <Input
                            id="phone"
                            placeholder="+91 98765 43210"
                            value={newAddress.phone}
                            onChange={(e) =>
                              setNewAddress({ ...newAddress, phone: e.target.value })
                            }
                          />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="street">Street Address</Label>
                        <Textarea
                          id="street"
                          placeholder="123 Main Street, Apt 4B"
                          value={newAddress.street}
                          onChange={(e) =>
                            setNewAddress({ ...newAddress, street: e.target.value })
                          }
                        />
                      </div>
                      <div className="grid grid-cols-3 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="city">City</Label>
                          <Input
                            id="city"
                            placeholder="Mumbai"
                            value={newAddress.city}
                            onChange={(e) =>
                              setNewAddress({ ...newAddress, city: e.target.value })
                            }
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="state">State</Label>
                          <Input
                            id="state"
                            placeholder="Maharashtra"
                            value={newAddress.state}
                            onChange={(e) =>
                              setNewAddress({ ...newAddress, state: e.target.value })
                            }
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="pincode">PIN Code</Label>
                          <Input
                            id="pincode"
                            placeholder="400001"
                            value={newAddress.pincode}
                            onChange={(e) =>
                              setNewAddress({ ...newAddress, pincode: e.target.value })
                            }
                          />
                        </div>
                      </div>
                      <Button className="w-full" onClick={() => toast.success('Address saved!')}>
                        Save Address
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
              </CardContent>
            </Card>

            {/* Payment Method */}
            <Card>
              <CardHeader>
                <CardTitle className="font-heading flex items-center gap-2">
                  <CreditCard className="h-5 w-5 text-primary" />
                  Payment Method
                </CardTitle>
              </CardHeader>
              <CardContent>
                <RadioGroup
                  value={paymentMethod}
                  onValueChange={setPaymentMethod}
                  className="space-y-3"
                >
                  {paymentMethods.map((method) => (
                    <div
                      key={method.id}
                      className={`relative flex items-center gap-4 p-4 rounded-lg border-2 transition-colors cursor-pointer ${
                        paymentMethod === method.id
                          ? 'border-primary bg-primary/5'
                          : 'border-border hover:border-primary/50'
                      }`}
                    >
                      <RadioGroupItem value={method.id} id={method.id} />
                      <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center">
                        <method.icon className="h-5 w-5 text-primary" />
                      </div>
                      <Label htmlFor={method.id} className="flex-1 cursor-pointer">
                        <span className="font-medium text-foreground block">{method.name}</span>
                        <span className="text-sm text-muted-foreground">{method.description}</span>
                      </Label>
                      {paymentMethod === method.id && (
                        <Check className="h-5 w-5 text-primary" />
                      )}
                    </div>
                  ))}
                </RadioGroup>

                {/* Pay Online info */}
                {paymentMethod === 'online' && (
                  <div className="mt-4 p-4 rounded-lg bg-primary/5 border border-primary/20">
                    <div className="flex items-start gap-3">
                      <ShieldCheck className="h-5 w-5 text-primary mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-foreground">Secure Payment via Razorpay</p>
                        <p className="text-sm text-muted-foreground mt-1">
                          You'll be redirected to Razorpay's secure payment page to complete your payment using Credit/Debit Cards, UPI, Net Banking, or Wallets.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* COD info */}
                {paymentMethod === 'cod' && (
                  <div className="mt-4 p-4 rounded-lg bg-muted/50 border border-border">
                    <div className="flex items-start gap-3">
                      <Truck className="h-5 w-5 text-muted-foreground mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-foreground">Cash on Delivery</p>
                        <p className="text-sm text-muted-foreground mt-1">
                          Pay with cash when your order is delivered. Please keep exact change ready.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Order Summary */}
          <div className="lg:col-span-1">
            <Card className="sticky top-24">
              <CardHeader>
                <CardTitle className="font-heading">Order Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Order Items */}
                <Accordion type="single" collapsible defaultValue="items">
                  <AccordionItem value="items" className="border-0">
                    <AccordionTrigger className="py-2 hover:no-underline">
                      <span className="text-sm">
                        {cartItems.length} {cartItems.length === 1 ? 'item' : 'items'}
                      </span>
                    </AccordionTrigger>
                    <AccordionContent>
                      <div className="space-y-3">
                        {cartItems.map((item) => (
                          <div key={item.id} className="flex gap-3">
                            <div className="w-16 h-16 rounded-lg overflow-hidden bg-muted shrink-0">
                              <img
                                src={item.image}
                                alt={item.name}
                                className="w-full h-full object-cover"
                              />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-foreground line-clamp-1">
                                {item.name}
                              </p>
                              <p className="text-xs text-muted-foreground">Qty: {item.quantity}</p>
                              <p className="text-sm font-medium text-foreground">
                                {formatPrice(item.price * item.quantity)}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>

                <Separator />

                {/* Price Breakdown */}
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Subtotal</span>
                    <span className="font-medium">{formatPrice(cartTotal)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Shipping</span>
                    <span className="font-medium">
                      {shipping === 0 ? (
                        <span className="text-success">Free</span>
                      ) : (
                        formatPrice(shipping)
                      )}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">GST (18%)</span>
                    <span className="font-medium">{formatPrice(tax)}</span>
                  </div>
                </div>

                <Separator />

                <div className="flex justify-between">
                  <span className="font-heading font-bold text-lg">Total</span>
                  <span className="font-heading font-bold text-lg text-primary">
                    {formatPrice(finalTotal)}
                  </span>
                </div>

                <Button
                  className="w-full bg-primary hover:bg-primary-dark shadow-lg shadow-primary/25"
                  size="lg"
                  onClick={handlePlaceOrder}
                  disabled={isProcessing}
                  data-testid="place-order-btn"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      Processing...
                    </>
                  ) : paymentMethod === 'online' ? (
                    <>
                      Pay {formatPrice(finalTotal)}
                      <ChevronRight className="ml-2 h-4 w-4" />
                    </>
                  ) : (
                    <>
                      Place Order
                      <ChevronRight className="ml-2 h-4 w-4" />
                    </>
                  )}
                </Button>

                {/* Trust Badges */}
                <div className="flex items-center justify-center gap-4 pt-4">
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <ShieldCheck className="h-4 w-4 text-success" />
                    Secure Checkout
                  </div>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Truck className="h-4 w-4 text-primary" />
                    Fast Delivery
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CheckoutPage;
