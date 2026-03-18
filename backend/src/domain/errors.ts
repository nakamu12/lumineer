export class DomainError extends Error {
  constructor(message: string) {
    super(message)
    this.name = this.constructor.name
  }
}

export class NotFoundError extends DomainError {}

export class ConflictError extends DomainError {}

export class AuthenticationError extends DomainError {}
