package Ejercicio_04;

public class Pastura extends Cereal {

    public Pastura(String nombre) {
        super(nombre);
    }

    @Override
    public boolean puedeSembrarseEn(Lote lote) {

        if (!super.puedeSembrarseEn(lote)) {
            return false;
        }

        // Verifica si se sembró otra pastura anteriormente
        if (lote.getCerealAnterior() instanceof Pastura) {
            return false;
        }

        return true;
    }
}
