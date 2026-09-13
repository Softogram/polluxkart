# Maintenance page for polluxkart.com

`index.html` in this folder is shown at polluxkart.com while the store is rebuilt.
It replaces the old app, which still loaded third-party Emergent scripts and could not reach its backend.

The page is one static file with no JavaScript, so there is nothing on it to break or leak.
Its only outside request is Google Fonts, the same fonts the store already uses.
Its colours, fonts and logo are copied unchanged from the store's existing theme, which stays as it is.
It tells search engines not to index it (`noindex`), so the relaunch starts with a clean search listing.

## Adding a business contact card later

The page ships without contact details until they are confirmed.
Before the store relaunches, Indian e-commerce rules and the payment gateway's website review expect seller details to be visible.
To add them, paste this block into `index.html` just before `</main>`, fill in the real values, and upload again.
The styles for it are already in the page.

```html
<section class="card" aria-labelledby="contact-heading">
  <h2 id="contact-heading">Need help with an earlier order?</h2>
  <dl>
    <dt>Business</dt>
    <dd>LEGAL BUSINESS NAME</dd>
    <dt>Address</dt>
    <dd>REGISTERED ADDRESS, CITY, STATE, PINCODE</dd>
    <dt>GSTIN</dt>
    <dd>GSTIN</dd>
    <dt>Email</dt>
    <dd><a href="mailto:SUPPORT_EMAIL">SUPPORT_EMAIL</a></dd>
    <dt>Phone</dt>
    <dd><a href="tel:+91XXXXXXXXXX">+91 XXXXX XXXXX</a></dd>
  </dl>
</section>
```

## How it is hosted

The site is served by AWS CloudFront (a content delivery network that caches files close to visitors) from the S3 bucket (AWS file storage) `polluxkart-frontend-ap-south-1`.
CloudFront sends every missing path to `index.html`, so every old URL shows this page.

## How to upload

1. Turn on bucket versioning once, so every replaced file stays recoverable:
   ```
   aws s3api put-bucket-versioning --bucket polluxkart-frontend-ap-south-1 --versioning-configuration Status=Enabled
   ```
2. Remove the old app files and upload the page:
   ```
   aws s3 rm s3://polluxkart-frontend-ap-south-1 --recursive
   aws s3 cp ops/maintenance/index.html s3://polluxkart-frontend-ap-south-1/index.html --content-type "text/html; charset=utf-8" --cache-control "no-cache"
   ```
3. Make CloudFront serve the new file right away, instead of its cached copy:
   ```
   aws cloudfront create-invalidation --distribution-id E236X7BM3NXSSQ --paths "/*"
   ```

## How to check it worked

```
curl -s https://polluxkart.com | grep -c emergent
```

That should print `0`.
Open the site on a phone too.
