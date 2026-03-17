import { describe, it, expect } from "vitest"
import { UserSettingsFactory } from "../../../domain/entities/user_settings.ts"

describe("UserSettingsFactory", () => {
  const validParams = {
    id: "settings-id",
    rerankerStrategy: "none",
    contextFormat: "json",
    topK: 10,
    similarityThreshold: 0.7,
  }

  it("creates valid settings with defaults", () => {
    const settings = UserSettingsFactory.create(validParams)
    expect(settings.rerankerStrategy).toBe("none")
    expect(settings.contextFormat).toBe("json")
    expect(settings.topK).toBe(10)
    expect(settings.similarityThreshold).toBe(0.7)
  })

  it("accepts all valid reranker strategies", () => {
    for (const strategy of ["none", "heuristic", "cross-encoder"]) {
      const settings = UserSettingsFactory.create({ ...validParams, rerankerStrategy: strategy })
      expect(settings.rerankerStrategy).toBe(strategy)
    }
  })

  it("accepts both context formats", () => {
    for (const format of ["json", "toon"]) {
      const settings = UserSettingsFactory.create({ ...validParams, contextFormat: format })
      expect(settings.contextFormat).toBe(format)
    }
  })

  it("accepts valid top_k values", () => {
    for (const topK of [5, 10, 20]) {
      const settings = UserSettingsFactory.create({ ...validParams, topK })
      expect(settings.topK).toBe(topK)
    }
  })

  it("throws on invalid reranker strategy", () => {
    expect(() =>
      UserSettingsFactory.create({ ...validParams, rerankerStrategy: "invalid" }),
    ).toThrow("Invalid reranker strategy: invalid")
  })

  it("throws on invalid context format", () => {
    expect(() => UserSettingsFactory.create({ ...validParams, contextFormat: "xml" })).toThrow(
      "Invalid context format: xml",
    )
  })

  it("throws on invalid top_k value", () => {
    expect(() => UserSettingsFactory.create({ ...validParams, topK: 15 })).toThrow(
      "Invalid top_k value: 15",
    )
  })

  it("throws on similarity threshold below 0.5", () => {
    expect(() => UserSettingsFactory.create({ ...validParams, similarityThreshold: 0.3 })).toThrow(
      "Invalid similarity threshold: 0.3",
    )
  })

  it("throws on similarity threshold above 0.9", () => {
    expect(() => UserSettingsFactory.create({ ...validParams, similarityThreshold: 0.95 })).toThrow(
      "Invalid similarity threshold: 0.95",
    )
  })

  it("accepts boundary similarity thresholds", () => {
    const low = UserSettingsFactory.create({ ...validParams, similarityThreshold: 0.5 })
    expect(low.similarityThreshold).toBe(0.5)
    const high = UserSettingsFactory.create({ ...validParams, similarityThreshold: 0.9 })
    expect(high.similarityThreshold).toBe(0.9)
  })
})
