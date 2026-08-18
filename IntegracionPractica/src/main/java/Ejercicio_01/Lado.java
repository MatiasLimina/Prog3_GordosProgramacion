package Ejercicio_01;

public class Lado {
    private Punto puntoA;
    private Punto puntoB;

    public Lado(Punto puntoA, Punto puntoB) {
        this.puntoA = puntoA;
        this.puntoB = puntoB;
    }

    public Punto getPuntoA() {
        return puntoA;
    }

    public void setPuntoA(Punto puntoA) {
        this.puntoA = puntoA;
    }

    public Punto getPuntoB() {
        return puntoB;
    }

    public void setPuntoB(Punto puntoB) {
        this.puntoB = puntoB;
    }

    public double calcularLongitud() {
        double dx = puntoB.getX() - puntoA.getX();
        double dy = puntoB.getY() - puntoA.getY();
        return Math.sqrt(dx * dx + dy * dy);
    }

}
