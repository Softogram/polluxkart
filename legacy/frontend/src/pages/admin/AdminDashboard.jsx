import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Package,
  ShoppingCart,
  Users,
  DollarSign,
  TrendingUp,
  AlertCircle,
  ArrowUpRight,
  Loader2,
  Trash2,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '../../components/ui/alert-dialog';
import AdminService from '../../services/adminService';
import { formatPrice } from '../../utils/currency';
import { toast } from 'sonner';

const AdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCleaningDb, setIsCleaningDb] = useState(false);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await AdminService.getDashboardStats();
      setStats(data);
    } catch (error) {
      toast.error('Failed to load dashboard stats');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCleanDatabase = async () => {
    setIsCleaningDb(true);
    try {
      const result = await AdminService.cleanSeedData();
      toast.success('Database cleaned successfully!');
      console.log('Cleanup result:', result);
      // Reload stats after cleanup
      await loadStats();
    } catch (error) {
      toast.error(error.message || 'Failed to clean database');
      console.error('Cleanup error:', error);
    } finally {
      setIsCleaningDb(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const statCards = [
    {
      title: 'Total Revenue',
      value: formatPrice(stats?.total_revenue || 0),
      icon: DollarSign,
      color: 'bg-green-500',
      subtext: `${formatPrice(stats?.revenue_today || 0)} today`,
    },
    {
      title: 'Total Orders',
      value: stats?.total_orders || 0,
      icon: ShoppingCart,
      color: 'bg-blue-500',
      subtext: `${stats?.orders_today || 0} today`,
    },
    {
      title: 'Total Products',
      value: stats?.total_products || 0,
      icon: Package,
      color: 'bg-purple-500',
      subtext: `${stats?.low_stock_products || 0} low stock`,
    },
    {
      title: 'Total Users',
      value: stats?.total_users || 0,
      icon: Users,
      color: 'bg-orange-500',
      subtext: 'Registered users',
    },
  ];

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500">Welcome to PolluxKart Admin Panel</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statCards.map((stat, index) => (
          <Card key={index}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 mb-1">{stat.title}</p>
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                  <p className="text-xs text-gray-400 mt-1">{stat.subtext}</p>
                </div>
                <div className={`w-12 h-12 rounded-lg ${stat.color} flex items-center justify-center`}>
                  <stat.icon className="h-6 w-6 text-white" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Pending Orders Alert */}
        {stats?.pending_orders > 0 && (
          <Card className="border-orange-200 bg-orange-50">
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center">
                  <AlertCircle className="h-5 w-5 text-orange-600" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-orange-900">Pending Orders</h3>
                  <p className="text-sm text-orange-700 mb-3">
                    You have {stats.pending_orders} order(s) waiting to be processed
                  </p>
                  <Link to="/admin/orders?status=pending">
                    <Button size="sm" variant="outline" className="border-orange-300 text-orange-700">
                      View Orders
                      <ArrowUpRight className="ml-1 h-4 w-4" />
                    </Button>
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Low Stock Alert */}
        {stats?.low_stock_products > 0 && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                  <Package className="h-5 w-5 text-red-600" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-red-900">Low Stock Alert</h3>
                  <p className="text-sm text-red-700 mb-3">
                    {stats.low_stock_products} product(s) are running low on stock
                  </p>
                  <Link to="/admin/products">
                    <Button size="sm" variant="outline" className="border-red-300 text-red-700">
                      Manage Inventory
                      <ArrowUpRight className="ml-1 h-4 w-4" />
                    </Button>
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Quick Links */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <Link to="/admin/products">
              <Button variant="outline" className="w-full h-auto py-4 flex-col gap-2">
                <Package className="h-6 w-6" />
                <span>Add Product</span>
              </Button>
            </Link>
            <Link to="/admin/orders">
              <Button variant="outline" className="w-full h-auto py-4 flex-col gap-2">
                <ShoppingCart className="h-6 w-6" />
                <span>View Orders</span>
              </Button>
            </Link>
            <Link to="/admin/categories">
              <Button variant="outline" className="w-full h-auto py-4 flex-col gap-2">
                <TrendingUp className="h-6 w-6" />
                <span>Categories</span>
              </Button>
            </Link>
            <Link to="/admin/promotions">
              <Button variant="outline" className="w-full h-auto py-4 flex-col gap-2">
                <DollarSign className="h-6 w-6" />
                <span>Promotions</span>
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Database Management */}
      <Card className="mt-6 border-red-200">
        <CardHeader>
          <CardTitle className="text-red-700 flex items-center gap-2">
            <Trash2 className="h-5 w-5" />
            Database Management
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600 mb-4">
            Remove all seed/test data from the database. This will delete all products, categories, 
            orders, and other data except user accounts. Use this to clean up the database after testing.
          </p>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button 
                variant="destructive" 
                className="gap-2"
                data-testid="clean-database-btn"
              >
                <Trash2 className="h-4 w-4" />
                Clean Database
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                <AlertDialogDescription>
                  This action cannot be undone. This will permanently delete all:
                  <ul className="list-disc ml-6 mt-2 space-y-1">
                    <li>Products</li>
                    <li>Categories</li>
                    <li>Orders</li>
                    <li>Reviews</li>
                    <li>Carts & Wishlists</li>
                    <li>Promotions</li>
                    <li>Inventory data</li>
                  </ul>
                  <p className="mt-2 font-semibold">User accounts will be preserved.</p>
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={handleCleanDatabase}
                  disabled={isCleaningDb}
                  className="bg-red-600 hover:bg-red-700"
                  data-testid="confirm-clean-database-btn"
                >
                  {isCleaningDb ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Cleaning...
                    </>
                  ) : (
                    'Yes, Clean Database'
                  )}
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminDashboard;
