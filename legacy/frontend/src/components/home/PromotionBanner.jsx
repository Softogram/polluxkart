import React from 'react';
import { ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Carousel, CarouselContent, CarouselItem, CarouselNext, CarouselPrevious } from '../ui/carousel';
import { promotions } from '../../data/products';

const PromotionBanner = () => {
  return (
    <section className="py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="font-heading text-2xl font-bold text-foreground">Current Offers</h2>
          <p className="text-sm text-muted-foreground mt-1">Don't miss out on these amazing deals</p>
        </div>
      </div>
      
      <Carousel
        opts={{
          align: 'start',
          loop: true,
        }}
        className="w-full"
      >
        <CarouselContent className="-ml-4">
          {promotions.map((promo) => (
            <CarouselItem key={promo.id} className="pl-4 md:basis-1/2 lg:basis-1/3">
              <div className="relative h-48 rounded-2xl overflow-hidden group">
                {/* Background Image */}
                <img
                  src={promo.image}
                  alt={promo.title}
                  className="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                />
                {/* Gradient Overlay */}
                <div className="absolute inset-0 bg-gradient-to-r from-foreground/80 via-foreground/60 to-transparent" />
                
                {/* Content */}
                <div className="relative h-full p-6 flex flex-col justify-between text-background">
                  <div>
                    <Badge className="bg-accent text-accent-foreground mb-2">
                      {promo.discount} OFF
                    </Badge>
                    <h3 className="font-heading text-xl font-bold">{promo.title}</h3>
                    <p className="text-sm text-background/80 mt-1">{promo.subtitle}</p>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-background/70">Use code:</span>
                      <Badge variant="outline" className="border-background/30 text-background font-mono">
                        {promo.code}
                      </Badge>
                    </div>
                    <Link to="/store">
                      <Button
                        size="sm"
                        variant="secondary"
                        className="bg-background/20 hover:bg-background/30 text-background border-0 backdrop-blur-sm"
                      >
                        Shop Now
                        <ArrowRight className="ml-1 h-3 w-3" />
                      </Button>
                    </Link>
                  </div>
                </div>
              </div>
            </CarouselItem>
          ))}
        </CarouselContent>
        <CarouselPrevious className="-left-2 bg-background/90 border-border hover:bg-background" />
        <CarouselNext className="-right-2 bg-background/90 border-border hover:bg-background" />
      </Carousel>
    </section>
  );
};

export default PromotionBanner;
