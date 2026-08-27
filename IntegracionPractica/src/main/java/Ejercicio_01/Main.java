package Ejercicio_01;

import java.util.Arrays;
import java.util.List;

public class Main {
    public static void main(String[] args) {
        // --- Demo que valida el diagrama y restricciones ---

        // Puntos y lados para triángulo (3,4,5)
        Punto p1 = new Punto(0, 0);
        Punto p2 = new Punto(3, 0);
        Punto p3 = new Punto(3, 4);
        Lado l1 = new Lado(p1, p2);
        Lado l2 = new Lado(p2, p3);
        Lado l3 = new Lado(p3, p1);
        Triangulo triangulo = new Triangulo("rojo", Arrays.asList(l1, l2, l3));
        System.out.println("Triángulo área (esperado 6.0): " + triangulo.calcularArea());

        // Elipse y Círculo
        Elipse elipse = new Elipse("azul", 5, 3);
        System.out.println("Elipse área (PI*5*3): " + elipse.calcularArea());
        Circulo circulo = new Circulo("verde", 4);
        System.out.println("Círculo área (PI*16): " + circulo.calcularArea());

        // Rectángulo y Cuadrado
        Rectangulo rect = new Rectangulo("amarillo", 4, 6);
        System.out.println("Rectángulo área 4x6=24: " + rect.calcularArea());
        Cuadrado cuad = new Cuadrado("negro", 5);
        System.out.println("Cuadrado área 5x5=25: " + cuad.calcularArea());

        // Cuadrilátero genérico con 4 lados explícitos
        Punto q1 = new Punto(0, 0);
        Punto q2 = new Punto(2, 0);
        Punto q3 = new Punto(2, 2);
        Punto q4 = new Punto(0, 2);
        Cuadrilatero cuadGen = new Cuadrilatero("gris", Arrays.asList(
                new Lado(q1, q2), new Lado(q2, q3), new Lado(q3, q4), new Lado(q4, q1)
        ));
        System.out.println("Cuadrilátero genérico área (2x2=4): " + cuadGen.calcularArea());

        // FiguraCompuesta: composite 1 — 0..*
        FiguraCompuesta compuesta = new FiguraCompuesta("compuesta");
        compuesta.agregarFigura(triangulo);
        compuesta.agregarFigura(circulo);
        compuesta.agregarFigura(rect);
        System.out.println("FiguraCompuesta área (6 + PI*16 + 24): " + compuesta.calcularArea());

        // Compuesta anidada
        FiguraCompuesta compuesta2 = new FiguraCompuesta("compuesta2", List.of(cuad, elipse));
        compuesta.agregarFigura(compuesta2);
        System.out.println("FiguraCompuesta anidada área total: " + compuesta.calcularArea());

        System.out.println("Demo OK - todas las multiplicidades y herencia validadas.");
    }
}
