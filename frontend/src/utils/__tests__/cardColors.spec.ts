import { getCardBackgroundColor, getCardStyle } from '../cardColors';

describe('cardColors', () => {
  describe('getCardBackgroundColor', () => {
    describe('known banks', () => {
      it('returns correct color for ICBC', () => {
        expect(getCardBackgroundColor('ICBC')).toBe('#D90000');
      });

      it('returns correct color for Santander', () => {
        expect(getCardBackgroundColor('Santander')).toBe('#EC0000');
      });

      it('returns correct color for BBVA', () => {
        expect(getCardBackgroundColor('BBVA')).toBe('#004481');
      });

      it('returns correct color for Galicia', () => {
        expect(getCardBackgroundColor('Galicia')).toBe('#FF6600');
      });

      it('returns correct color for Naranja', () => {
        expect(getCardBackgroundColor('Naranja')).toBe('#FF5000');
      });

      it('returns correct color for Ualá (with accent)', () => {
        expect(getCardBackgroundColor('Ualá')).toBe('#7B2CBF');
      });

      it('returns correct color for Uala (without accent)', () => {
        expect(getCardBackgroundColor('Uala')).toBe('#7B2CBF');
      });

      it('returns correct color for Mercado Pago', () => {
        expect(getCardBackgroundColor('Mercado Pago')).toBe('#009EE3');
      });

      it('returns correct color for Banco Nación (with accent)', () => {
        expect(getCardBackgroundColor('Banco Nación')).toBe('#003087');
      });

      it('returns correct color for Banco Nacion (without accent)', () => {
        expect(getCardBackgroundColor('Banco Nacion')).toBe('#003087');
      });

      it('returns correct color for Bersa', () => {
        expect(getCardBackgroundColor('Bersa')).toBe('#007A33');
      });

      it('returns correct color for Banco de Santa Fe', () => {
        expect(getCardBackgroundColor('Banco de Santa Fe')).toBe('#00843D');
      });

      it('returns correct color for Banco Ciudad', () => {
        expect(getCardBackgroundColor('Banco Ciudad')).toBe('#FFB800');
      });
    });

    describe('case-insensitivity', () => {
      it('handles uppercase ICBC', () => {
        expect(getCardBackgroundColor('ICBC')).toBe('#D90000');
      });

      it('handles lowercase icbc', () => {
        expect(getCardBackgroundColor('icbc')).toBe('#D90000');
      });

      it('handles mixed case Icbc', () => {
        expect(getCardBackgroundColor('Icbc')).toBe('#D90000');
      });

      it('handles whitespace padding around ICBC', () => {
        expect(getCardBackgroundColor('  ICBC  ')).toBe('#D90000');
      });
    });

    describe('accent handling', () => {
      it('maps Ualá (with accent) to purple', () => {
        expect(getCardBackgroundColor('Ualá')).toBe('#7B2CBF');
      });

      it('maps Uala (without accent) to purple', () => {
        expect(getCardBackgroundColor('Uala')).toBe('#7B2CBF');
      });

      it('maps Banco Nación (with accent) to navy', () => {
        expect(getCardBackgroundColor('Banco Nación')).toBe('#003087');
      });

      it('maps Banco Nacion (without accent) to navy', () => {
        expect(getCardBackgroundColor('Banco Nacion')).toBe('#003087');
      });
    });

    describe('space variations', () => {
      it('handles Mercado Pago with spaces', () => {
        expect(getCardBackgroundColor('Mercado Pago')).toBe('#009EE3');
      });

      it('handles MercadoPago without spaces', () => {
        expect(getCardBackgroundColor('MercadoPago')).toBe('#009EE3');
      });

      it('handles Banco de Santa Fe with spaces', () => {
        expect(getCardBackgroundColor('Banco de Santa Fe')).toBe('#00843D');
      });

      it('handles BancodeSantaFe without spaces', () => {
        expect(getCardBackgroundColor('BancodeSantaFe')).toBe('#00843D');
      });

      it('handles Banco Nación with spaces and accent', () => {
        expect(getCardBackgroundColor('Banco Nación')).toBe('#003087');
      });

      it('handles BancoNacion without spaces', () => {
        expect(getCardBackgroundColor('BancoNacion')).toBe('#003087');
      });
    });

    describe('edge cases', () => {
      it('returns fallback gray for unknown bank', () => {
        expect(getCardBackgroundColor('Unknown Bank')).toBe('#6B7280');
      });

      it('returns fallback gray for empty string', () => {
        expect(getCardBackgroundColor('')).toBe('#6B7280');
      });

      it('returns fallback gray for whitespace-only string', () => {
        expect(getCardBackgroundColor('   ')).toBe('#6B7280');
      });
    });
  });

  describe('getCardStyle', () => {
    it('returns style object with ICBC color', () => {
      expect(getCardStyle('ICBC')).toEqual({ background: '#D90000' });
    });

    it('returns style object with Santander color', () => {
      expect(getCardStyle('Santander')).toEqual({ background: '#EC0000' });
    });

    it('returns style object with Ualá (accent) color', () => {
      expect(getCardStyle('Ualá')).toEqual({ background: '#7B2CBF' });
    });

    it('returns style object with fallback gray for unknown bank', () => {
      expect(getCardStyle('Unknown Bank')).toEqual({ background: '#6B7280' });
    });

    it('returns style object with fallback gray for empty string', () => {
      expect(getCardStyle('')).toEqual({ background: '#6B7280' });
    });

    it('handles case-insensitive input', () => {
      expect(getCardStyle('icbc')).toEqual({ background: '#D90000' });
      expect(getCardStyle('ICBC')).toEqual({ background: '#D90000' });
    });

    it('handles space variations', () => {
      expect(getCardStyle('Mercado Pago')).toEqual({ background: '#009EE3' });
      expect(getCardStyle('MercadoPago')).toEqual({ background: '#009EE3' });
    });

    it('handles accent variations', () => {
      expect(getCardStyle('Ualá')).toEqual({ background: '#7B2CBF' });
      expect(getCardStyle('Uala')).toEqual({ background: '#7B2CBF' });
    });
  });
});
