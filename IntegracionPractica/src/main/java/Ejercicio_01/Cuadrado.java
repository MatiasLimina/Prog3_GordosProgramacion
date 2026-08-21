package Ejercicio_01;

import java.util.List;

/**
 * Cuadrado es un Rectángulo con todos los lados iguales.
 * Invariante R5: base == altura == lado
 */
public class Cuadrado extends Rectangulo {

    private double lado;

    public Cuadrado(String color, double lado) {
        super(color, lado, lado);
        if (lado <= 0) {
            throw new IllegalArgumentException("Lado debe ser > 0");
        }
        this.lado = lado;
    }

    /**
     * Constructor alternativo con lados explícitos.
     */
    public Cuadrado(String color, List<Lado> lados) {
        super(color, lados);
        double l1 = lados.get(0).calcularLongitud();
        // Validar que los 4 lados sean iguales
        for (Lado l : lados) {
            if (Math.abs(l.calcularLongitud() - l1) > 1e-6) {
                throw new IllegalArgumentException("Cuadrado requiere 4 lados iguales");
            }
        }
        this.lado = l1;
    }

    public double getLado() {
        return lado;
    }

    @Override
    public double calcularArea() {
        return lado * lado;
    }
}
