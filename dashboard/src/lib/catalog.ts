/**
 * Display metadata for the legal instruments in the corpus.
 *
 * Keys match CORE_ACTS in download_core_acts.py (and therefore GET /api/acts); filenames match
 * data/raw_acts and the `source_file` of chat sources. `coverage` describes what is actually
 * indexed. Update it whenever the corpus in data/raw_acts changes.
 */

export type InstrumentCategory = "act" | "subordinate" | "case_law";

export interface Instrument {
  key: string;
  filename: string;
  title: string;
  short: string;
  category: InstrumentCategory;
  summary: string;
  coverage: string;
}

export const INSTRUMENTS: Instrument[] = [
  {
    key: "constitution",
    filename: "constitution_act_108_of_1996.txt",
    title: "Constitution of the Republic of South Africa, 1996",
    short: "Constitution",
    category: "act",
    summary: "The supreme law, including the Bill of Rights.",
    coverage: "Sections 9, 10, 14, 23, 32 and 33",
  },
  {
    key: "bcea",
    filename: "bcea_act_75_of_1997.txt",
    title: "Basic Conditions of Employment Act 75 of 1997",
    short: "BCEA",
    category: "act",
    summary: "Minimum conditions of employment: working time, overtime and leave.",
    coverage: "Sections 6, 9, 10, 20, 22, 25 and 27",
  },
  {
    key: "lra",
    filename: "lra_act_66_of_1995.txt",
    title: "Labour Relations Act 66 of 1995",
    short: "LRA",
    category: "act",
    summary: "Freedom of association, dismissal and unfair labour practices.",
    coverage: "Sections 1, 4, 185, 186 and 188; Schedule 8 items 1 and 4",
  },
  {
    key: "eea",
    filename: "eea_act_55_of_1998.txt",
    title: "Employment Equity Act 55 of 1998",
    short: "EEA",
    category: "act",
    summary: "Prohibition of unfair discrimination in employment.",
    coverage: "Section 6",
  },
  {
    key: "nmwa",
    filename: "nmwa_act_9_of_2018.txt",
    title: "National Minimum Wage Act 9 of 2018",
    short: "NMWA",
    category: "act",
    summary: "Entitlement to the national minimum wage.",
    coverage: "Section 4 (the current rate is not included)",
  },
  {
    key: "ohsa",
    filename: "ohsa_act_85_of_1993.txt",
    title: "Occupational Health and Safety Act 85 of 1993",
    short: "OHSA",
    category: "act",
    summary: "General duties of employers to provide a safe workplace.",
    coverage: "Section 8",
  },
  {
    key: "popia",
    filename: "popia_act_4_of_2013.txt",
    title: "Protection of Personal Information Act 4 of 2013",
    short: "POPIA",
    category: "act",
    summary: "Conditions for lawfully processing personal information.",
    coverage: "Sections 1, 5, 8, 9, 10, 11, 14, 19 and 22",
  },
  {
    key: "cpa",
    filename: "cpa_act_68_of_2008.txt",
    title: "Consumer Protection Act 68 of 2008",
    short: "CPA",
    category: "act",
    summary: "Consumer rights, cooling-off and the implied warranty of quality.",
    coverage: "Sections 3, 16, 54, 55 and 56",
  },
  {
    key: "nca",
    filename: "nca_act_34_of_2005.txt",
    title: "National Credit Act 34 of 2005",
    short: "NCA",
    category: "act",
    summary: "Reckless credit and debt review.",
    coverage: "Sections 3, 80, 81 and 86",
  },
  {
    key: "companies_act",
    filename: "companies_act_71_of_2008.txt",
    title: "Companies Act 71 of 2008",
    short: "Companies Act",
    category: "act",
    summary: "Directors' duties and liability, and business rescue.",
    coverage: "Sections 1, 22, 66, 75, 76, 77 and 129",
  },
  {
    key: "ppa",
    filename: "ppa_act_22_of_2019.txt",
    title: "Property Practitioners Act 22 of 2019",
    short: "PPA",
    category: "act",
    summary: "Duties of estate agents and other property practitioners.",
    coverage: "Section 67",
  },
  {
    key: "ecta",
    filename: "ecta_act_25_of_2002.txt",
    title: "Electronic Communications and Transactions Act 25 of 2002",
    short: "ECTA",
    category: "act",
    summary: "Legal recognition of electronic data messages.",
    coverage: "Section 11",
  },
  {
    key: "popia_regs",
    filename: "popia_regulations.txt",
    title: "POPIA General Regulations",
    short: "POPIA Regulations",
    category: "subordinate",
    summary: "Responsibilities of information officers.",
    coverage: "Regulation 4",
  },
  {
    key: "lra_harassment_code",
    filename: "lra_harassment_code.txt",
    title: "Code of Good Practice on the Prevention and Elimination of Harassment in the Workplace",
    short: "Harassment Code",
    category: "subordinate",
    summary: "The test for workplace harassment.",
    coverage: "Item 4",
  },
  {
    key: "ccma_rules",
    filename: "ccma_rules.txt",
    title: "Rules for the Conduct of Proceedings before the CCMA",
    short: "CCMA Rules",
    category: "subordinate",
    summary: "How to refer a dispute to the CCMA.",
    coverage: "Rule 11",
  },
  {
    key: "case_law_concourt",
    filename: "case_law_concourt.txt",
    title: "Constitutional Court judgments",
    short: "ConCourt",
    category: "case_law",
    summary: "Mahlangu v Minister of Labour: domestic workers and COIDA.",
    coverage: "One judgment summary",
  },
  {
    key: "case_law_sca",
    filename: "case_law_sca.txt",
    title: "Supreme Court of Appeal judgments",
    short: "SCA",
    category: "case_law",
    summary: "AfriForum v University of the Free State: university language policy.",
    coverage: "One judgment summary",
  },
];

export const CATEGORY_LABELS: Record<InstrumentCategory, string> = {
  act: "Acts",
  subordinate: "Regulations, codes and rules",
  case_law: "Case law",
};

const BY_KEY = new Map(INSTRUMENTS.map((i) => [i.key.toLowerCase(), i]));
const BY_FILENAME = new Map(INSTRUMENTS.map((i) => [i.filename, i]));

export function instrumentByKey(key: string): Instrument | undefined {
  return BY_KEY.get(key.toLowerCase());
}

export function instrumentByFilename(filename: string): Instrument | undefined {
  return BY_FILENAME.get(filename);
}

/**
 * Options for narrowing chat retrieval. `value` is sent as act_filter and must stay a substring of
 * the indexed Act titles (the API matches case-insensitively).
 */
export const ACT_FILTERS: { value: string; label: string }[] = [
  { value: "All Acts", label: "All sources" },
  { value: "Basic Conditions of Employment Act", label: "BCEA" },
  { value: "Labour Relations Act", label: "LRA" },
  { value: "Protection of Personal Information Act", label: "POPIA" },
  { value: "Consumer Protection Act", label: "CPA" },
  { value: "National Credit Act", label: "NCA" },
  { value: "Companies Act", label: "Companies Act" },
];
