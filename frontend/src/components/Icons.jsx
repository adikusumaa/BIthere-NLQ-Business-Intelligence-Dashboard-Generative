/**
 * Minimal SVG icon set.
 * No emojis, no external icon library.
 */

const base = {
  display: "inline-block",
  verticalAlign: "middle",
  flexShrink: 0,
};

export function SendIcon({ size = 18, color = "#FFFFFF" }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      style={base}
      aria-hidden="true"
    >
      <path
        d="M12 4V20M12 4L5 11M12 4L19 11"
        stroke={color}
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function CloseIcon({ size = 18, color = "#8E8E93" }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      style={base}
      aria-hidden="true"
    >
      <path
        d="M6 6L18 18M18 6L6 18"
        stroke={color}
        strokeWidth="2.2"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function ChevronRightIcon({ size = 16, color = "#C7C7CC" }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      style={base}
      aria-hidden="true"
    >
      <path
        d="M9 6L15 12L9 18"
        stroke={color}
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function PlusIcon({ size = 18, color = "#007AFF" }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      style={base}
      aria-hidden="true"
    >
      <path
        d="M12 5V19M5 12H19"
        stroke={color}
        strokeWidth="2.2"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function MenuIcon({ size = 20, color = "#007AFF" }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      style={base}
      aria-hidden="true"
    >
      <circle cx="5" cy="12" r="1.6" fill={color} />
      <circle cx="12" cy="12" r="1.6" fill={color} />
      <circle cx="19" cy="12" r="1.6" fill={color} />
    </svg>
  );
}

export function PanelIcon({ size = 18, color = "#007AFF" }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      style={base}
      aria-hidden="true"
    >
      <rect
        x="3"
        y="4"
        width="18"
        height="16"
        rx="3"
        stroke={color}
        strokeWidth="1.8"
      />
      <path
        d="M15 4V20"
        stroke={color}
        strokeWidth="1.8"
      />
    </svg>
  );
}

export function FileIcon({ size = 18, color = "#007AFF" }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      style={base}
      aria-hidden="true"
    >
      <path
        d="M6 3H14L19 8V21H6V3Z"
        stroke={color}
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <path
        d="M14 3V8H19"
        stroke={color}
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function MailIcon({ size = 18, color = "#007AFF" }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      style={base}
      aria-hidden="true"
    >
      <rect
        x="3"
        y="5"
        width="18"
        height="14"
        rx="3"
        stroke={color}
        strokeWidth="1.8"
      />
      <path
        d="M4 7L12 13L20 7"
        stroke={color}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function ChatIcon({ size = 18, color = "#007AFF" }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      style={base}
      aria-hidden="true"
    >
      <path
        d="M4 5H20V17H13L9 21V17H4V5Z"
        stroke={color}
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function UserIcon({ size = 18, color = "#8E8E93" }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      style={base}
      aria-hidden="true"
    >
      <circle cx="12" cy="8" r="4" stroke={color} strokeWidth="1.8" />
      <path
        d="M4 21C4 16.5 7.5 14 12 14C16.5 14 20 16.5 20 21"
        stroke={color}
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function TrashIcon({ size = 16, color = "#FF3B30" }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      style={base}
      aria-hidden="true"
    >
      <path
        d="M5 7H19M10 7V5H14V7M7 7L8 20H16L17 7"
        stroke={color}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}