import React from 'react';
import { Link } from 'react-router-dom';
import { Mail, Phone, MapPin, Facebook, Twitter, Instagram, Youtube } from 'lucide-react';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { Separator } from '../ui/separator';
import Logo from '../brand/Logo';

const Footer = () => {
  const footerLinks = {
    shop: [
      { name: 'All Products', path: '/store' },
      { name: 'Electronics', path: '/store?category=electronics' },
      { name: 'Fashion', path: '/store?category=fashion' },
      { name: 'Home & Lifestyle', path: '/store?category=home' },
    ],
    support: [
      { name: 'Help Center', path: '#' },
      { name: 'Track Order', path: '/orders' },
      { name: 'Shipping Info', path: '#' },
      { name: 'Returns', path: '#' },
    ],
    company: [
      { name: 'About Us', path: '#' },
      { name: 'Careers', path: '#' },
      { name: 'Press', path: '#' },
      { name: 'Blog', path: '#' },
    ],
  };

  const socialLinks = [
    { icon: Facebook, href: '#', label: 'Facebook' },
    { icon: Twitter, href: '#', label: 'Twitter' },
    { icon: Instagram, href: '#', label: 'Instagram' },
    { icon: Youtube, href: '#', label: 'YouTube' },
  ];

  return (
    <footer className="bg-muted/30 border-t border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Main Footer Content */}
        <div className="py-12 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
          {/* Brand & Newsletter */}
          <div className="lg:col-span-2">
            <Link to="/" className="inline-block mb-4">
              <Logo size="default" />
            </Link>
            <p className="text-sm text-muted-foreground mb-6 max-w-sm">
              Your one-stop destination for electronics, fashion, home essentials, and more. 
              Quality products, great prices, delivered to your doorstep.
            </p>
            <div className="space-y-3">
              <p className="text-sm font-medium">Subscribe to our newsletter</p>
              <form className="flex gap-2 max-w-sm">
                <Input
                  type="email"
                  placeholder="Enter your email"
                  className="flex-1 bg-background"
                />
                <Button type="submit" className="shrink-0">
                  Subscribe
                </Button>
              </form>
            </div>
          </div>

          {/* Shop Links */}
          <div>
            <h3 className="font-heading font-semibold text-sm mb-4">Shop</h3>
            <ul className="space-y-3">
              {footerLinks.shop.map((link) => (
                <li key={link.name}>
                  <Link
                    to={link.path}
                    className="text-sm text-muted-foreground hover:text-primary transition-colors"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Support Links */}
          <div>
            <h3 className="font-heading font-semibold text-sm mb-4">Support</h3>
            <ul className="space-y-3">
              {footerLinks.support.map((link) => (
                <li key={link.name}>
                  <Link
                    to={link.path}
                    className="text-sm text-muted-foreground hover:text-primary transition-colors"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company Links */}
          <div>
            <h3 className="font-heading font-semibold text-sm mb-4">Company</h3>
            <ul className="space-y-3">
              {footerLinks.company.map((link) => (
                <li key={link.name}>
                  <Link
                    to={link.path}
                    className="text-sm text-muted-foreground hover:text-primary transition-colors"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <Separator />

        {/* Contact & Social */}
        <div className="py-6 flex flex-col sm:flex-row justify-between items-center gap-4">
          <div className="flex flex-wrap justify-center sm:justify-start gap-6 text-sm text-muted-foreground">
            <a href="mailto:support@polluxkart.com" className="flex items-center gap-2 hover:text-primary transition-colors">
              <Mail className="h-4 w-4" />
              support@polluxkart.com
            </a>
            <a href="tel:+1234567890" className="flex items-center gap-2 hover:text-primary transition-colors">
              <Phone className="h-4 w-4" />
              +1 (234) 567-890
            </a>
          </div>
          <div className="flex items-center gap-4">
            {socialLinks.map((social) => (
              <a
                key={social.label}
                href={social.href}
                aria-label={social.label}
                className="w-9 h-9 rounded-full bg-muted flex items-center justify-center text-muted-foreground hover:bg-primary hover:text-primary-foreground transition-colors"
              >
                <social.icon className="h-4 w-4" />
              </a>
            ))}
          </div>
        </div>

        <Separator />

        {/* Copyright */}
        <div className="py-6 flex flex-col sm:flex-row justify-between items-center gap-4 text-sm text-muted-foreground">
          <p>&copy; {new Date().getFullYear()} PolluxKart. All rights reserved.</p>
          <div className="flex gap-6">
            <Link to="#" className="hover:text-primary transition-colors">Privacy Policy</Link>
            <Link to="#" className="hover:text-primary transition-colors">Terms of Service</Link>
            <Link to="#" className="hover:text-primary transition-colors">Cookies</Link>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
