export type Account = {
  id: string;
  email: string;
  display_name: string;
  roles: string[];
  permissions: string[];
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
};
export type AdminSession = {
  account: Account;
  csrf_token: string;
  expires_at: string;
  session_id: string;
  created_at: string;
};
export type SafeSession = {
  id: string;
  created_at: string;
  last_used_at: string;
  expires_at: string;
  current: boolean;
};
export type RoleInfo = { name: string; permissions: string[] };
export type DraftContent = {
  organization_name: string;
  organization_description: string;
  organization_type: string;
  service_name: string;
  description: string;
  eligibility: string | null;
  languages: string[];
  accessibility: string | null;
  emergency_availability: boolean;
  categories: string[];
  contact_phone: string | null;
  contact_email: string | null;
  website: string | null;
  location_name: string | null;
  city: string | null;
  region: string | null;
  postal_code: string | null;
  service_area: string | null;
  hours: string | null;
  transportation: string | null;
  application_instructions: string | null;
  source_name: string;
  source_url: string;
  source_organization: string;
};
export type GovernedResource = {
  id: string;
  state: string;
  revision: number;
  content: DraftContent;
  owner_id: string;
  assigned_reviewer_id: string | null;
  public_service_id: string | null;
  created_at: string;
  updated_at: string;
};

let csrfToken = "";
export function setCsrf(value: string) {
  csrfToken = value;
}

export async function adminFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(`/api/admin/${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      "content-type": "application/json",
      ...(init.method && init.method !== "GET"
        ? { "x-csrf-token": csrfToken }
        : {}),
      ...init.headers,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw Object.assign(new Error(body?.error?.message ?? "Request failed"), {
      status: response.status,
    });
  }
  return (response.status === 204 ? undefined : await response.json()) as T;
}

export async function loadSession() {
  const session = await adminFetch<AdminSession>("auth/session");
  setCsrf(session.csrf_token);
  return session;
}
