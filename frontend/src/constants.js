export const STATUSES = [
  { value: "not_contacted", label: "Not contacted" },
  { value: "contacted", label: "Contacted" },
  { value: "replied", label: "Replied" },
  { value: "meeting_booked", label: "Meeting booked" },
  { value: "closed", label: "Closed" },
];

export const STATUS_LABEL = Object.fromEntries(STATUSES.map((s) => [s.value, s.label]));

export const TONES = [
  { value: "friendly", label: "Friendly" },
  { value: "professional", label: "Professional" },
  { value: "concise", label: "Concise" },
];
