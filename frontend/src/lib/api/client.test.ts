import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "./client";

describe("Frontend API Client", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("handles login and stores Bearer token in sessionStorage", async () => {
    const fakeTokenResponse = {
      access_token: "test.jwt.token",
      token_type: "bearer",
      operator_id: "sec-admin-1",
      role: "admin",
      target_account_id: "000000000000",
      expires_in_seconds: 3600,
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => fakeTokenResponse,
    });

    const res = await api.login("sec-admin-1", "admin");
    expect(res.access_token).toBe("test.jwt.token");
    expect(sessionStorage.getItem("falcon_auth_token")).toBe("test.jwt.token");
  });

  it("clears token on logout", () => {
    sessionStorage.setItem("falcon_auth_token", "active-token");
    api.logout();
    expect(sessionStorage.getItem("falcon_auth_token")).toBeNull();
  });

  it("throws descriptive error when fetch response is not ok", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
      json: async () => ({ detail: "Invalid token" }),
    });

    await expect(api.getHealth()).rejects.toThrow("Invalid token");
  });
});
