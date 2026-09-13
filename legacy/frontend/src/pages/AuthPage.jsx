import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, Lock, User, Eye, EyeOff, ArrowLeft, Phone, ChevronDown, Loader2, CheckCircle2, KeyRound } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Checkbox } from '../components/ui/checkbox';
import { Separator } from '../components/ui/separator';
import { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { ScrollArea } from '../components/ui/scroll-area';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import Logo from '../components/brand/Logo';
import { countryCodes, getCountryByCode } from '../data/countryCodes';
import OTPService from '../services/otpService';
import { apiFetch } from '../services/apiConfig';

const AuthPage = () => {
  const navigate = useNavigate();
  const { login, signup, isLoading } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [loginMethod, setLoginMethod] = useState('email');
  const [loginCountryCode, setLoginCountryCode] = useState('+91');
  const [signupCountryCode, setSignupCountryCode] = useState('+91');
  
  // Forgot Password States
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [forgotPasswordData, setForgotPasswordData] = useState({
    identifier: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [resettingPassword, setResettingPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  
  // OTP States
  const [loginOtpSent, setLoginOtpSent] = useState(false);
  const [loginOtpVerified, setLoginOtpVerified] = useState(false);
  const [loginOtp, setLoginOtp] = useState(['', '', '', '', '', '']);
  const [signupOtpSent, setSignupOtpSent] = useState(false);
  const [signupOtpVerified, setSignupOtpVerified] = useState(false);
  const [signupOtp, setSignupOtp] = useState(['', '', '', '', '', '']);
  const [sendingOtp, setSendingOtp] = useState(false);
  const [verifyingOtp, setVerifyingOtp] = useState(false);
  const [otpTimer, setOtpTimer] = useState(0);
  
  // OTP input refs
  const loginOtpRefs = useRef([]);
  const signupOtpRefs = useRef([]);
  
  const [loginData, setLoginData] = useState({ 
    email: '', 
    phone: '',
    password: '' 
  });
  const [signupData, setSignupData] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
    agreeTerms: false,
  });

  const loginCountry = getCountryByCode(loginCountryCode);
  const signupCountry = getCountryByCode(signupCountryCode);

  // OTP Timer countdown
  useEffect(() => {
    if (otpTimer > 0) {
      const timer = setTimeout(() => setOtpTimer(otpTimer - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [otpTimer]);

  // Handle OTP input change
  const handleOtpChange = (index, value, otpArray, setOtpArray, refs) => {
    // Only allow single digit
    const digit = value.replace(/\D/g, '').slice(-1);
    
    const newOtp = [...otpArray];
    newOtp[index] = digit;
    setOtpArray(newOtp);

    // Auto-focus next input when a digit is entered
    if (digit && index < 5) {
      setTimeout(() => {
        refs.current[index + 1]?.focus();
      }, 0);
    }
  };

  // Handle OTP paste
  const handleOtpPaste = (e, setOtpArray, refs) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').slice(0, 6);
    if (!/^\d+$/.test(pastedData)) return;

    const newOtp = pastedData.split('').concat(Array(6 - pastedData.length).fill(''));
    setOtpArray(newOtp.slice(0, 6));
    refs.current[Math.min(pastedData.length, 5)]?.focus();
  };

  // Handle OTP backspace
  const handleOtpKeyDown = (index, e, otpArray, setOtpArray, refs) => {
    if (e.key === 'Backspace' && !otpArray[index] && index > 0) {
      refs.current[index - 1]?.focus();
    }
  };

  // Send OTP using MongoDB backend
  const sendOtp = async (phone, isLogin = true) => {
    if (!phone || phone.length < 7) {
      toast.error('Please enter a valid phone number');
      return;
    }

    setSendingOtp(true);
    
    const fullPhoneNumber = `${isLogin ? loginCountryCode : signupCountryCode}${phone}`;
    
    try {
      const result = await OTPService.sendOTP(fullPhoneNumber);
      
      if (result.success) {
        if (isLogin) {
          setLoginOtpSent(true);
          setLoginOtp(['', '', '', '', '', '']);
          setLoginOtpVerified(false);
        } else {
          setSignupOtpSent(true);
          setSignupOtp(['', '', '', '', '', '']);
          setSignupOtpVerified(false);
        }
        
        setOtpTimer(30);
        toast.success(result.message || `OTP sent to ${fullPhoneNumber}`);
        
        // For development: fetch and show the OTP
        if (process.env.NODE_ENV === 'development') {
          const debug = await OTPService.debugGetOTP(fullPhoneNumber);
          if (debug?.otp?.code) {
            console.log(`[DEV] OTP for ${fullPhoneNumber}: ${debug.otp.code}`);
          }
        }
      } else {
        toast.error(result.message || 'Failed to send OTP');
      }
    } catch (error) {
      console.error('Error sending OTP:', error);
      toast.error('Failed to send OTP. Please try again.');
    } finally {
      setSendingOtp(false);
    }
  };

  // Verify OTP using MongoDB backend
  const verifyOtp = async (otp, isLogin = true) => {
    const otpString = otp.join('');
    if (otpString.length !== 6) {
      toast.error('Please enter complete 6-digit OTP');
      return false;
    }

    setVerifyingOtp(true);
    
    const fullPhoneNumber = isLogin 
      ? `${loginCountryCode}${loginData.phone}`
      : `${signupCountryCode}${signupData.phone}`;
    
    try {
      const result = await OTPService.verifyOTP(otpString, fullPhoneNumber);
      
      if (result.success) {
        if (isLogin) {
          setLoginOtpVerified(true);
        } else {
          setSignupOtpVerified(true);
        }
        
        toast.success(result.message || 'Phone number verified!');
        return true;
      } else {
        toast.error(result.message || 'Invalid OTP. Please try again.');
        return false;
      }
    } catch (error) {
      console.error('Error verifying OTP:', error);
      toast.error('Failed to verify OTP. Please try again.');
      return false;
    } finally {
      setVerifyingOtp(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    
    // OTP verification disabled - will be enabled when SMS service is integrated
    // if (loginMethod === 'phone') {
    //   if (!loginOtpVerified) {
    //     toast.error('Please verify your phone number first');
    //     return;
    //   }
    // }
    
    const identifier = loginMethod === 'email' ? loginData.email : `${loginCountryCode}${loginData.phone}`;
    
    if (!loginData.email && loginMethod === 'email') {
      toast.error('Please enter your email');
      return;
    }
    
    if (!loginData.phone && loginMethod === 'phone') {
      toast.error('Please enter your phone number');
      return;
    }
    
    if (!loginData.password) {
      toast.error('Please enter your password');
      return;
    }
    
    try {
      await login(identifier, loginData.password);
      toast.success('Welcome back!');
      navigate('/');
    } catch (error) {
      toast.error(error.message || 'Login failed. Please check your credentials.');
    }
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    
    if (!signupData.name || !signupData.phone || !signupData.password) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    // OTP verification disabled - will be enabled when SMS service is integrated
    // if (!signupOtpVerified) {
    //   toast.error('Please verify your phone number first');
    //   return;
    // }
    
    // Validate email if provided
    if (signupData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(signupData.email)) {
      toast.error('Please enter a valid email address');
      return;
    }
    
    if (signupData.password !== signupData.confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }
    
    if (signupData.password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    
    if (!signupData.agreeTerms) {
      toast.error('Please agree to the terms and conditions');
      return;
    }
    
    try {
      const fullPhone = `${signupCountryCode}${signupData.phone}`;
      await signup(signupData.name, signupData.email, fullPhone, signupData.password);
      toast.success('Account created successfully!');
      navigate('/');
    } catch (error) {
      toast.error(error.message || 'Signup failed. Please try again.');
    }
  };

  // Handle Forgot Password
  const handleForgotPassword = async (e) => {
    e.preventDefault();
    
    if (!forgotPasswordData.identifier) {
      toast.error('Please enter your email or phone number');
      return;
    }
    
    if (!forgotPasswordData.newPassword) {
      toast.error('Please enter a new password');
      return;
    }
    
    if (forgotPasswordData.newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    
    if (forgotPasswordData.newPassword !== forgotPasswordData.confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }
    
    setResettingPassword(true);
    
    try {
      const response = await apiFetch('/auth/reset-password', {
        method: 'POST',
        body: JSON.stringify({
          identifier: forgotPasswordData.identifier,
          new_password: forgotPasswordData.newPassword,
          confirm_password: forgotPasswordData.confirmPassword,
        }),
        includeAuth: false,
      });
      
      if (response.success) {
        toast.success(response.message || 'Password reset successfully!');
        setShowForgotPassword(false);
        setForgotPasswordData({ identifier: '', newPassword: '', confirmPassword: '' });
      }
    } catch (error) {
      toast.error(error.message || 'Failed to reset password');
    } finally {
      setResettingPassword(false);
    }
  };

  // Reset OTP state when phone number changes
  const handleLoginPhoneChange = (value) => {
    const cleaned = value.replace(/\D/g, '').slice(0, loginCountry.maxLength);
    setLoginData({ ...loginData, phone: cleaned });
    if (loginOtpSent) {
      setLoginOtpSent(false);
      setLoginOtpVerified(false);
      setLoginOtp(['', '', '', '', '', '']);
    }
  };

  const handleSignupPhoneChange = (value) => {
    const cleaned = value.replace(/\D/g, '').slice(0, signupCountry.maxLength);
    setSignupData({ ...signupData, phone: cleaned });
    if (signupOtpSent) {
      setSignupOtpSent(false);
      setSignupOtpVerified(false);
      setSignupOtp(['', '', '', '', '', '']);
    }
  };

  const CountryCodeSelector = ({ value, onChange, id }) => (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          className="flex items-center gap-1 px-2 h-10 rounded-r-none border-r-0 bg-muted/50 hover:bg-muted min-w-[90px]"
          data-testid={`country-code-${id}`}
        >
          <span className="text-base">{getCountryByCode(value).flag}</span>
          <span className="text-sm font-medium">{value}</span>
          <ChevronDown className="h-3 w-3 text-muted-foreground" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-[240px]">
        <ScrollArea className="h-[300px]">
          {countryCodes.map((country) => (
            <DropdownMenuItem
              key={country.code}
              onClick={() => onChange(country.code)}
              className="flex items-center gap-3 cursor-pointer"
            >
              <span className="text-lg">{country.flag}</span>
              <span className="flex-1 text-sm">{country.country}</span>
              <span className="text-sm text-muted-foreground">{country.code}</span>
            </DropdownMenuItem>
          ))}
        </ScrollArea>
      </DropdownMenuContent>
    </DropdownMenu>
  );

  // OTP Input Component - render inline to preserve refs
  const renderOtpInputs = (otp, setOtp, refs, disabled = false, prefix = 'otp') => (
    <div className="flex gap-2 justify-center">
      {[0, 1, 2, 3, 4, 5].map((index) => (
        <input
          key={index}
          ref={(el) => {
            if (refs.current) {
              refs.current[index] = el;
            }
          }}
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          maxLength={1}
          value={otp[index] || ''}
          onChange={(e) => handleOtpChange(index, e.target.value, otp, setOtp, refs)}
          onKeyDown={(e) => handleOtpKeyDown(index, e, otp, setOtp, refs)}
          onPaste={(e) => handleOtpPaste(e, setOtp, refs)}
          disabled={disabled}
          className="w-10 h-12 text-center text-lg font-semibold border border-input rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:opacity-50"
          data-testid={`${prefix}-input-${index}`}
          autoComplete="one-time-code"
        />
      ))}
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/5 via-background to-accent/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Link
          to="/"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-primary mb-8"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Home
        </Link>

        <div className="flex flex-col lg:flex-row items-center justify-center gap-12 min-h-[calc(100vh-200px)]">
          {/* Left Side - Branding */}
          <div className="flex-1 max-w-md text-center lg:text-left">
            <Link to="/" className="inline-block mb-6">
              <Logo size="large" />
            </Link>
            <h1 className="font-heading text-3xl lg:text-4xl font-bold text-foreground mb-4">
              Welcome to PolluxKart
            </h1>
            <p className="text-muted-foreground mb-8">
              Your one-stop destination for electronics, fashion, home essentials, and more.
              Join thousands of happy customers shopping with us.
            </p>
            <div className="flex flex-wrap gap-4 justify-center lg:justify-start">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <div className="w-8 h-8 rounded-full bg-success/10 flex items-center justify-center">
                  <span className="text-success">✓</span>
                </div>
                Free Shipping
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <div className="w-8 h-8 rounded-full bg-success/10 flex items-center justify-center">
                  <span className="text-success">✓</span>
                </div>
                Secure Payment
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <div className="w-8 h-8 rounded-full bg-success/10 flex items-center justify-center">
                  <span className="text-success">✓</span>
                </div>
                Easy Returns
              </div>
            </div>
          </div>

          {/* Right Side - Auth Form */}
          <div className="w-full max-w-md">
            <Card className="border-0 shadow-xl">
              <Tabs defaultValue="login" className="w-full">
                <div className="px-6 pt-6">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="login" data-testid="login-tab">Login</TabsTrigger>
                    <TabsTrigger value="signup" data-testid="signup-tab">Sign Up</TabsTrigger>
                  </TabsList>
                </div>

                <CardContent className="pt-6">
                  {/* Login Tab */}
                  <TabsContent value="login" className="mt-0">
                    <form onSubmit={handleLogin} className="space-y-4" data-testid="login-form">
                      {/* Login Method Selection */}
                      <div className="space-y-3">
                        <Label>Login with</Label>
                        <RadioGroup
                          value={loginMethod}
                          onValueChange={(value) => {
                            setLoginMethod(value);
                            setLoginOtpSent(false);
                            setLoginOtpVerified(false);
                          }}
                          className="flex gap-4"
                        >
                          <div className="flex items-center space-x-2">
                            <RadioGroupItem value="email" id="login-email-method" />
                            <Label htmlFor="login-email-method" className="font-normal cursor-pointer">
                              Email
                            </Label>
                          </div>
                          <div className="flex items-center space-x-2">
                            <RadioGroupItem value="phone" id="login-phone-method" />
                            <Label htmlFor="login-phone-method" className="font-normal cursor-pointer">
                              Phone
                            </Label>
                          </div>
                        </RadioGroup>
                      </div>

                      {/* Email/Phone Input */}
                      {loginMethod === 'email' ? (
                        <div className="space-y-2">
                          <Label htmlFor="login-email">Email</Label>
                          <div className="relative">
                            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                              id="login-email"
                              type="email"
                              placeholder="Enter your email"
                              value={loginData.email}
                              onChange={(e) =>
                                setLoginData({ ...loginData, email: e.target.value })
                              }
                              className="pl-10"
                              data-testid="login-email-input"
                            />
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          <Label htmlFor="login-phone">Phone Number</Label>
                          <div className="flex">
                            <CountryCodeSelector
                              value={loginCountryCode}
                              onChange={setLoginCountryCode}
                              id="login"
                            />
                            <Input
                              id="login-phone"
                              type="tel"
                              placeholder="Enter your phone number"
                              value={loginData.phone}
                              onChange={(e) => handleLoginPhoneChange(e.target.value)}
                              className="rounded-l-none"
                              maxLength={loginCountry.maxLength}
                              data-testid="login-phone-input"
                              disabled={false}
                            />
                          </div>
                          
                          {/* OTP Section disabled - will be enabled when SMS service is integrated */}
                          {/* 
                          {!loginOtpVerified && (
                            <div className="space-y-3">
                              ...OTP UI...
                            </div>
                          )}
                          */}
                        </div>
                      )}

                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <Label htmlFor="login-password">Password</Label>
                          <button
                            type="button"
                            onClick={() => setShowForgotPassword(true)}
                            className="text-xs text-primary hover:underline"
                            data-testid="forgot-password-link"
                          >
                            Forgot password?
                          </button>
                        </div>
                        <div className="relative">
                          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                          <Input
                            id="login-password"
                            type={showPassword ? 'text' : 'password'}
                            placeholder="Enter your password"
                            value={loginData.password}
                            onChange={(e) =>
                              setLoginData({ ...loginData, password: e.target.value })
                            }
                            className="pl-10 pr-10"
                            data-testid="login-password-input"
                          />
                          <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                          >
                            {showPassword ? (
                              <EyeOff className="h-4 w-4" />
                            ) : (
                              <Eye className="h-4 w-4" />
                            )}
                          </button>
                        </div>
                      </div>

                      <Button
                        type="submit"
                        className="w-full bg-primary hover:bg-primary-dark"
                        disabled={isLoading || (loginMethod === 'phone' && !loginOtpVerified)}
                        data-testid="login-submit-btn"
                      >
                        {isLoading ? 'Logging in...' : 'Login'}
                      </Button>
                    </form>

                    <div className="mt-6">
                      <div className="relative">
                        <Separator />
                        <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-card px-2 text-xs text-muted-foreground">
                          OR
                        </span>
                      </div>

                      <div className="mt-6 space-y-3">
                        <Button variant="outline" className="w-full" type="button">
                          <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
                            <path
                              fill="currentColor"
                              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                            />
                            <path
                              fill="currentColor"
                              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                            />
                            <path
                              fill="currentColor"
                              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                            />
                            <path
                              fill="currentColor"
                              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                            />
                          </svg>
                          Continue with Google
                        </Button>
                      </div>
                    </div>
                  </TabsContent>

                  {/* Signup Tab */}
                  <TabsContent value="signup" className="mt-0">
                    <form onSubmit={handleSignup} className="space-y-4" data-testid="signup-form">
                      <div className="space-y-2">
                        <Label htmlFor="signup-name">Full Name <span className="text-destructive">*</span></Label>
                        <div className="relative">
                          <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                          <Input
                            id="signup-name"
                            type="text"
                            placeholder="Enter your full name"
                            value={signupData.name}
                            onChange={(e) =>
                              setSignupData({ ...signupData, name: e.target.value })
                            }
                            className="pl-10"
                            data-testid="signup-name-input"
                          />
                        </div>
                      </div>

                      <div className="space-y-3">
                        <Label htmlFor="signup-phone">Phone Number <span className="text-destructive">*</span></Label>
                        <div className="flex">
                          <CountryCodeSelector
                            value={signupCountryCode}
                            onChange={setSignupCountryCode}
                            id="signup"
                          />
                          <Input
                            id="signup-phone"
                            type="tel"
                            placeholder="Enter your phone number"
                            value={signupData.phone}
                            onChange={(e) => handleSignupPhoneChange(e.target.value)}
                            className="rounded-l-none"
                            maxLength={signupCountry.maxLength}
                            data-testid="signup-phone-input"
                            disabled={false}
                          />
                        </div>
                        
                        {/* OTP Section disabled - will be enabled when SMS service is integrated */}
                        {/* 
                        {!signupOtpVerified && (
                          <div className="space-y-3">
                            ...OTP UI...
                          </div>
                        )}
                        */}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="signup-email">Email <span className="text-muted-foreground text-xs">(Optional)</span></Label>
                        <div className="relative">
                          <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                          <Input
                            id="signup-email"
                            type="email"
                            placeholder="Enter your email (optional)"
                            value={signupData.email}
                            onChange={(e) =>
                              setSignupData({ ...signupData, email: e.target.value })
                            }
                            className="pl-10"
                            data-testid="signup-email-input"
                          />
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="signup-password">Password <span className="text-destructive">*</span></Label>
                        <div className="relative">
                          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                          <Input
                            id="signup-password"
                            type={showPassword ? 'text' : 'password'}
                            placeholder="Create a password"
                            value={signupData.password}
                            onChange={(e) =>
                              setSignupData({ ...signupData, password: e.target.value })
                            }
                            className="pl-10 pr-10"
                            data-testid="signup-password-input"
                          />
                          <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                          >
                            {showPassword ? (
                              <EyeOff className="h-4 w-4" />
                            ) : (
                              <Eye className="h-4 w-4" />
                            )}
                          </button>
                        </div>
                        <p className="text-xs text-muted-foreground">Minimum 6 characters</p>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="confirm-password">Confirm Password <span className="text-destructive">*</span></Label>
                        <div className="relative">
                          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                          <Input
                            id="confirm-password"
                            type="password"
                            placeholder="Confirm your password"
                            value={signupData.confirmPassword}
                            onChange={(e) =>
                              setSignupData({
                                ...signupData,
                                confirmPassword: e.target.value,
                              })
                            }
                            className="pl-10"
                            data-testid="signup-confirm-password-input"
                          />
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="terms"
                          checked={signupData.agreeTerms}
                          onCheckedChange={(checked) =>
                            setSignupData({ ...signupData, agreeTerms: checked })
                          }
                          data-testid="signup-terms-checkbox"
                        />
                        <Label htmlFor="terms" className="text-sm font-normal">
                          I agree to the{' '}
                          <Link to="#" className="text-primary hover:underline">
                            Terms of Service
                          </Link>{' '}
                          and{' '}
                          <Link to="#" className="text-primary hover:underline">
                            Privacy Policy
                          </Link>
                        </Label>
                      </div>

                      <Button
                        type="submit"
                        className="w-full bg-primary hover:bg-primary-dark"
                        disabled={isLoading}
                        data-testid="signup-submit-btn"
                      >
                        {isLoading ? 'Creating account...' : 'Create Account'}
                      </Button>
                    </form>
                  </TabsContent>
                </CardContent>
              </Tabs>
            </Card>
          </div>
        </div>
      </div>

      {/* Forgot Password Dialog */}
      <Dialog open={showForgotPassword} onOpenChange={setShowForgotPassword}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <KeyRound className="h-5 w-5 text-primary" />
              Reset Password
            </DialogTitle>
            <DialogDescription>
              Enter your email or phone number and create a new password.
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleForgotPassword} className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label htmlFor="reset-identifier">Email or Phone Number</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="reset-identifier"
                  type="text"
                  placeholder="Enter your email or phone"
                  value={forgotPasswordData.identifier}
                  onChange={(e) =>
                    setForgotPasswordData({ ...forgotPasswordData, identifier: e.target.value })
                  }
                  className="pl-10"
                  data-testid="reset-identifier-input"
                />
              </div>
              <p className="text-xs text-muted-foreground">
                For phone, include country code (e.g., +919876543210)
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="reset-new-password">New Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="reset-new-password"
                  type={showNewPassword ? 'text' : 'password'}
                  placeholder="Enter new password"
                  value={forgotPasswordData.newPassword}
                  onChange={(e) =>
                    setForgotPasswordData({ ...forgotPasswordData, newPassword: e.target.value })
                  }
                  className="pl-10 pr-10"
                  data-testid="reset-new-password-input"
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              <p className="text-xs text-muted-foreground">Minimum 6 characters</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="reset-confirm-password">Confirm New Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="reset-confirm-password"
                  type={showNewPassword ? 'text' : 'password'}
                  placeholder="Confirm new password"
                  value={forgotPasswordData.confirmPassword}
                  onChange={(e) =>
                    setForgotPasswordData({ ...forgotPasswordData, confirmPassword: e.target.value })
                  }
                  className="pl-10"
                  data-testid="reset-confirm-password-input"
                />
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <Button
                type="button"
                variant="outline"
                className="flex-1"
                onClick={() => {
                  setShowForgotPassword(false);
                  setForgotPasswordData({ identifier: '', newPassword: '', confirmPassword: '' });
                }}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                className="flex-1"
                disabled={resettingPassword}
                data-testid="reset-password-submit-btn"
              >
                {resettingPassword ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Resetting...
                  </>
                ) : (
                  'Reset Password'
                )}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AuthPage;
