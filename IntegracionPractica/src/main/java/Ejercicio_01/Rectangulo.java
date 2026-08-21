package Ejercicio_01;

import java.util.Arrays;
import java.util.List;

/**
 * Rectángulo es un Cuadrilátero con 4 ángulos rectos.
 * Invariante: lados opuestos iguales (base y altura).
 */
public class Rectangulo extends Cuadrilatero {

    private double base;
    private double altura;

    public Rectangulo(String color, double base, double altura) {
        super(color, crearLados(base, altura));
        if (base <= 0 || altura <= 0) {
            throw new IllegalArgumentException("Base y altura deben ser > 0");
        }
        this.base = base;
        this.altura = altura;
    }

    /**
     * Constructor alternativo recibiendo los 4 lados explícitos (validación de rectángulo).
     */
    public Rectangulo(String color, List<Lado> lados) {
        super(color, lados);
        // Validar que sea rectángulo: lados opuestos iguales (tolerancia)
        // Se asume orden consecutivo
        double l1 = lados.get(0).calcularLongitud();
        double l2 = lados.get(1).calcularLongitud();
        double l3 = lados.get(2).calcularLongitud();
        double l4 = lados.get(3).calcularLongitud();
        if (Math.abs(l1 - l3) > 1e-6 || Math.abs(l2 - l4) > 1e-6) {
            throw new IllegalArgumentException("Lados opuestos deben ser iguales para ser rectángulo");
        }
        this.base = l1;
        this.altura = l2;
    }

    private static List<Lado> crearLados(double base, double altura) {
        // Crear rectángulo canónico en origen (0,0) - (base, altura)
        Punto p1 = new Punto(0, 0);
        Punto p2 = new Punto(base, 0);
        Punto p3 = new Punto(base, altura);
        Punto p4 = new Punto(0, altura);
        return Arrays.asList(
                new Lado(p1, p2),
                new Lado(p2, p3),
                new Lado(p3, p4),
                new Lado(p4, p1)
        );
    }

    public double getBase() {
        return base;
    }

    public double getAltura() {
        return altura;
    }

    @Override
    public double calcularArea() {
        return base * altura;
    }
}
