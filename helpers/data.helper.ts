export class DataHelper {
  static generateEmail(prefix = 'test'): string {
    return `${prefix}.${Date.now()}@testdomain.com`;
  }

  static generatePassword(length = 10): string {
    const chars = 'ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789!@#$';
    return Array.from({ length }, () =>
      chars[Math.floor(Math.random() * chars.length)]
    ).join('');
  }

  static randomString(length = 8): string {
    return Math.random().toString(36).substring(2, 2 + length);
  }

  static timestamp(): string {
    return new Date().toISOString().replace(/[:.]/g, '-');
  }

  static boundaries = {
    emptyString:           '',
    singleChar:            'a',
    maxLength255:          'a'.repeat(255),
    sqlInjection:          "'; DROP TABLE users; --",
    xssPayload:            '<script>alert(1)</script>',
    specialChars:          '!@#$%^&*()',
    whitespaceOnly:        '   ',
  };
}