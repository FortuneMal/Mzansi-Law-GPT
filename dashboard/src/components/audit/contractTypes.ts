import type { ContractType } from "@/lib/api";

export interface ContractTypeOption {
  value: ContractType;
  label: string;
  description: string;
  /** Compliance areas the API checks for this type (see the domains in api_server.audit_contract_endpoint). */
  areas: string[];
}

const CONSUMER_AREAS = [
  "Consumer rights and quality of goods (CPA)",
  "Cooling-off after direct marketing (CPA)",
  "Customer personal information (POPIA)",
  "Penalties and liability disclaimers",
];

export const CONTRACT_TYPES: ContractTypeOption[] = [
  {
    value: "auto",
    label: "Detect automatically",
    description: "The opening of the document is used to decide which checks apply.",
    areas: [],
  },
  {
    value: "employment",
    label: "Employment contract",
    description: "Working time, leave, employee data and termination.",
    areas: [
      "Working hours and overtime (BCEA)",
      "Annual, sick, maternity and family leave (BCEA)",
      "Employee personal information (POPIA)",
      "Termination and disciplinary procedure (LRA)",
    ],
  },
  {
    value: "lease",
    label: "Residential lease",
    description: "Consumer protections, penalties and tenant data.",
    areas: CONSUMER_AREAS,
  },
  {
    value: "consumer_terms",
    label: "Consumer terms and conditions",
    description: "Service agreements and standard terms for consumers.",
    areas: CONSUMER_AREAS,
  },
];
