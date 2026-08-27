package Ejercicio_01;

import java.util.Objects;

public class Lado {
    private Punto puntoA;
    private Punto puntoB;

    /**
     * @param puntoA extremo A (no null)
     * @param puntoB extremo B (no null, distinto de A)
     * Restricción R2: exactamente 2 puntos no nulos y distintos.
     */
    public Lado(Punto puntoA, Punto puntoB) {
        Objects.requireNonNull(puntoA, "puntoA no puede ser null");
        Objects.requireNonNull(puntoB, "puntoB no puede ser null");
        if (puntoA.equals(puntoB)) {
            throw new IllegalArgumentException("Un lado no puede tener sus dos puntos iguales: " + puntoA);
        }
        this.puntoA = puntoA;
        this.puntoB = puntoB;
    }

    public Punto getPuntoA() {
        return puntoA;
    }

    public void setPuntoA(Punto puntoA) {
        Objects.requireNonNull(puntoA, "puntoA no puede ser null");
        this.puntoA = puntoA;
    }

    public Punto getPuntoB() {
        return puntoB;
    }

    public void setPuntoB(Punto puntoB) {
        Objects.requireNonNull(puntoB, "puntoB no puede ser null");
        this.puntoB = puntoB;
    }

    public double calcularLongitud() {
        double dx = puntoB.getX() - puntoA.getX();
        double dy = puntoB.getY() - puntoA.getY();
        return Math.sqrt(dx * dx + dy * dy);
    }

    @Override
    public String toString() {
        return "Lado[" + puntoA + " -> " + puntoB + "]";
    }
}
