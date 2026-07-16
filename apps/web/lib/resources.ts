export type Category = {
  slug: string;
  name: string;
  description: string | null;
};
export type Verification = {
  status: "verified" | "needs_reverification";
  last_checked_at: string;
  may_be_stale: boolean;
  next_due_at: string | null;
  freshness:
    | "current"
    | "due_soon"
    | "due"
    | "overdue"
    | "critically_stale"
    | "unknown";
};
export type Contact = {
  channel_type: string;
  label: string;
  value: string;
  is_primary: boolean;
};
export type Location = {
  display_name: string;
  address_line_1: string | null;
  address_line_2: string | null;
  city: string | null;
  region: string | null;
  postal_code: string | null;
  country: string;
  service_area: string | null;
  transportation: string | null;
  accessibility: string | null;
  hours: string | null;
  timezone: string;
};
export type ServiceItem = {
  id: string;
  organization_name: string;
  name: string;
  description: string;
  categories: Category[];
  location_summary: string | null;
  languages: string[];
  accessibility: string | null;
  primary_contact: Contact | null;
  verification: Verification;
};
export type ServiceList = {
  items: ServiceItem[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
};
export type ServiceDetail = {
  id: string;
  name: string;
  description: string;
  eligibility: string | null;
  required_documents: string | null;
  cost_information: string | null;
  languages: string[];
  accessibility: string | null;
  application_instructions: string | null;
  appointment_requirements: string | null;
  emergency_availability: boolean;
  organization: {
    public_name: string;
    website: string | null;
    public_phone: string | null;
    public_email: string | null;
  };
  categories: Category[];
  locations: Location[];
  contacts: Contact[];
  sources: {
    name: string;
    url: string;
    organization: string;
    last_checked_at: string;
  }[];
  verification: Verification;
};

export function formatChecked(value: string): string {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeZone: "UTC",
  }).format(new Date(value));
}
