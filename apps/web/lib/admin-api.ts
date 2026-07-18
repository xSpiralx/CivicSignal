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
export type AuditEvent = {
  id: string;
  actor_id: string | null;
  action: string;
  subject_type: string;
  subject_id: string | null;
  summary: string;
  created_at: string;
};
export type DraftContent = {
  organization_name: string;
  organization_description: string;
  organization_type: string;
  service_name: string;
  description: string;
  eligibility: string | null;
  required_documents: string | null;
  cost_information: string | null;
  languages: string[];
  accessibility: string | null;
  emergency_availability: boolean;
  remote_service_available: boolean;
  categories: string[];
  contact_phone: string | null;
  contact_email: string | null;
  website: string | null;
  location_name: string | null;
  city: string | null;
  region: string | null;
  postal_code: string | null;
  country: string;
  timezone: string | null;
  service_area: string | null;
  hours: string | null;
  transportation: string | null;
  application_instructions: string | null;
  source_name: string;
  source_url: string;
  source_organization: string;
  source_type: string;
  source_retrieved_at: string | null;
  source_notes: string | null;
  source_public: boolean;
  source_supports_changed_fields: boolean;
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
export type Correction = {
  id: string;
  service_id: string;
  category: string;
  description: string;
  reporter_name: string | null;
  reporter_email: string | null;
  status: string;
  assigned_reviewer_id: string | null;
  duplicate_of_id: string | null;
  task_id: string | null;
  resolution_reason: string | null;
  resolved_at: string | null;
  version: number;
  submitted_at: string;
};
export type ReverificationTask = {
  id: string;
  service_id: string;
  resource_id: string | null;
  published_revision_id: string | null;
  trigger_source: string;
  reason: string;
  freshness_state: string;
  due_at: string;
  status: string;
  assigned_verifier_id: string | null;
  claimed_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  outcome: string | null;
  evidence_summary: string | null;
  contact_attempt_summary: string | null;
  source_references: string[] | null;
  notes: string | null;
  version: number;
  created_at: string;
};
export type Proposal = {
  task_id: string;
  task_version: number;
  resource_id: string;
  published_revision: number;
  proposed_revision: number;
  published_content: DraftContent;
  proposed_content: DraftContent;
  changed_fields: string[];
  blocking_errors: string[];
  warnings: string[];
  ready: boolean;
};
export type ImportCandidate = {
  id: string;
  batch_id: string;
  source_identifier: string;
  source: {
    stable_identifier: string;
    name: string;
    publishing_organization: string;
    source_url: string;
    license_name: string | null;
    license_url: string | null;
    attribution_requirement: string | null;
  };
  content: DraftContent;
  raw_content: Record<string, unknown> | null;
  source_url: string | null;
  source_record_updated_at: string | null;
  dataset_updated_at: string | null;
  retrieved_at: string;
  city: string | null;
  county: string | null;
  region: string | null;
  postal_code: string | null;
  categories: string[];
  service_area_type: string;
  nationwide: boolean;
  remote: boolean;
  risk_classification: string;
  duplicate_classification: string;
  conflict_status: string;
  validation_status: string;
  validation_result: Record<string, unknown>;
  review_status: string;
  reviewer_id: string | null;
  review_decision: string | null;
  governed_resource_id: string | null;
  version: number;
  created_at: string;
  updated_at: string;
  audit_history?: { action: string; summary: string; created_at: string }[];
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
