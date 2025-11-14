/**
 * Map Apify Google Maps result to company schema
 * Matches Python _map_apify_result logic from app/services/apify_service.py
 */

interface ApifyResult {
  title?: string;
  url?: string;
  phone?: string;
  website?: string;
  address?: string;
  location?: {
    lat?: number;
    lng?: number;
  };
  rating?: number;
  reviewsCount?: number;
  reviews?: any[];
  images?: Array<{ url?: string }>;
  category?: string;
  description?: string;
  openingHours?: any;
  [key: string]: any;
}

interface CompanyData {
  name: string;
  phone_primary: string;
  website?: string;
  google_business_url: string;
  address_street: string;
  address_city: string;
  address_state: string;
  address_zip: string;
  rating?: number;
  review_count?: number;
  hours?: any;
  latitude?: number;
  longitude?: number;
  photos?: string[];
  category?: string;
  description?: string;
  reviews?: any[];
  source: string;
}

export function mapApifyResult(item: ApifyResult): CompanyData | null {
  try {
    // Extract basic information
    const title = item.title || "";
    const googleMapsUrl = item.url || "";

    // Validate required fields
    if (!title || !googleMapsUrl) {
      return null;
    }

    // Extract phone
    const phone = item.phone || "";

    // Extract website
    let website = item.website || "";
    if (website && !website.startsWith("http")) {
      website = `https://${website}`;
    }

    // Parse address - match Python logic
    const address = item.address || "";
    const addressParts = address.split(",").map((p) => p.trim());
    
    let street = "";
    let city = "";
    let state = "";
    let zipCode = "";

    if (addressParts.length >= 3) {
      street = addressParts[0] || "";
      city = addressParts[1] || "";
      const stateZip = addressParts[addressParts.length - 1] || "";
      // Try to extract state and zip
      const parts = stateZip.split(/\s+/);
      if (parts.length >= 2) {
        state = parts[0] || "";
        zipCode = parts[parts.length - 1] || "";
      } else if (stateZip.length === 2) {
        state = stateZip;
      }
    } else if (addressParts.length === 2) {
      street = addressParts[0] || "";
      city = addressParts[1] || "";
    } else {
      street = address;
    }

    // Extract location coordinates
    const latitude = item.location?.lat;
    const longitude = item.location?.lng;

    // Extract images/photos
    const photos: string[] = [];
    if (item.images && Array.isArray(item.images)) {
      item.images.forEach((img) => {
        if (img.url) {
          photos.push(img.url);
        }
      });
    }

    // Extract rating and reviews
    const rating = item.rating;
    const reviewCount = item.reviewsCount || 0;
    const reviews = item.reviews || [];

    // Extract hours
    const hours = item.openingHours || null;

    // Extract category and description
    const category = item.category || null;
    const description = item.description || null;

    // Build result
    const result: CompanyData = {
      name: title,
      phone_primary: phone,
      website: website || undefined,
      google_business_url: googleMapsUrl,
      address_street: street || "",
      address_city: city || "",
      address_state: state || "",
      address_zip: zipCode || "",
      source: "apify_google_maps",
    };

    // Add optional fields
    if (rating !== undefined && rating !== null) {
      result.rating = rating;
    }

    if (reviewCount > 0) {
      result.review_count = reviewCount;
    }

    if (hours) {
      result.hours = hours;
    }

    if (latitude !== undefined && latitude !== null) {
      result.latitude = latitude;
    }

    if (longitude !== undefined && longitude !== null) {
      result.longitude = longitude;
    }

    if (photos.length > 0) {
      result.photos = photos;
    }

    if (category) {
      result.category = category;
    }

    if (description) {
      result.description = description;
    }

    if (reviews.length > 0) {
      result.reviews = reviews.slice(0, 5); // Store first 5 reviews
    }

    return result;
  } catch (error) {
    console.error("Error mapping Apify result:", error);
    return null;
  }
}

