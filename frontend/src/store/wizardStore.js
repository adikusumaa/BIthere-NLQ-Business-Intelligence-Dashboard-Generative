/**
 * Setup wizard state: current step + step data + persistence.
 */

import { create } from "zustand";
import { api } from "../services/api";

export const WIZARD_STEPS = [
  { id: 1, key: "account", title: "Account & Workspace" },
  { id: 2, key: "api_keys", title: "API Keys" },
  { id: 3, key: "data_source", title: "Data Source" },
  { id: 4, key: "dataset_upload", title: "Dataset Upload" },
  { id: 5, key: "schema_builder", title: "Schema Builder" },
  { id: 6, key: "knowledge_base", title: "Knowledge Base" },
];

export const useWizardStore = create((set, get) => ({
  currentStep: 1,
  stepData: {},
  completedSteps: {},
  setupCompleted: false,
  loading: false,

  setStep: (step) => set({ currentStep: step }),

  setStepData: (stepKey, data) =>
    set((s) => ({
      stepData: { ...s.stepData, [stepKey]: { ...s.stepData[stepKey], ...data } },
    })),

  loadState: async (workspaceId) => {
    set({ loading: true });
    try {
      const state = await api.getWizardState(workspaceId);
      const progress = state.setup_progress || {};
      const completed = {};
      let maxStep = 1;
      for (const [k, v] of Object.entries(progress)) {
        if (v?.completed) {
          completed[Number(k)] = true;
          maxStep = Math.max(maxStep, Number(k));
        }
      }
      set({
        completedSteps: completed,
        currentStep: Math.min(maxStep + 1, WIZARD_STEPS.length),
        setupCompleted: state.setup_completed || false,
        loading: false,
      });
    } catch (err) {
      set({ loading: false });
      console.error("Failed to load wizard state:", err);
    }
  },

  saveStep: async (workspaceId, step, data) => {
    await api.saveWizardStep(workspaceId, step, data);
    set((s) => ({
      completedSteps: { ...s.completedSteps, [step]: true },
      currentStep: Math.min(step + 1, WIZARD_STEPS.length),
    }));
  },

  complete: async (workspaceId) => {
    await api.completeWizard(workspaceId);
    set({ setupCompleted: true });
  },

  reset: () =>
    set({
      currentStep: 1,
      stepData: {},
      completedSteps: {},
      setupCompleted: false,
    }),
}));