import { describe, expect, it } from "vitest";

describe("mahjong booking scaffold", () => {
  it("has a smoke test target for the initial app shell", () => {
    expect("雀友局").toContain("雀友");
  });
});
