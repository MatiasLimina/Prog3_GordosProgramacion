package Ejercicio_01;

import java.util.List;

/**
 * Triángulo es un Polígono de exactamente 3 lados.
 * Restricción R1: 3 lados.
 */
public class Triangulo extends Poligono {

    public Triangulo(String color, List<Lado> lados) {
        super(color, lados);
        if (lados.size() != 3) {
            throw new IllegalArgumentException("Triángulo requiere exactamente 3 lados, recibido: " + lados.size());
        }
    }

    @Override
    public double calcularArea() {
        // Fórmula de Herón a partir de las longitudes de los lados
        double a = getLados().get(0).calcularLongitud();
        double b = getLados().get(1).calcularLongitud();
        double c = getLados().get(2).calcularLongitud();
        double s = (a + b + c) / 2.0;
        double area2 = s * (s - a) * (s - b) * (s - c);
        if (area2 < 0) area2 = 0; // por errores de redondeo en triángulos degenerados
        return Math.sqrt(area2);
    }
}
