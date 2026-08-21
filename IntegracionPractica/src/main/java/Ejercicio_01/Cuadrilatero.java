package Ejercicio_01;

import java.util.List;

/**
 * Cuadrilátero es un Polígono de exactamente 4 lados.
 * Extiende Poligono (no Figura directamente) — ver ANALISIS §2.
 * Puede ser abstracta si solo se permiten Rectángulos/Cuadrados,
 * pero se deja instanciable para cuadriláteros genéricos.
 */
public class Cuadrilatero extends Poligono {

    public Cuadrilatero(String color, List<Lado> lados) {
        super(color, lados);
        if (lados.size() != 4) {
            throw new IllegalArgumentException("Cuadrilátero requiere exactamente 4 lados, recibido: " + lados.size());
        }
    }

    @Override
    public double calcularArea() {
        // Área genérica por fórmula de Shoelace si los lados forman un polígono cerrado
        // Se reconstruyen los puntos en orden. Si no es posible, se lanza UnsupportedOperation
        // Para simplificar, si no hay geometría válida, retorna 0 y delega a subclases.
        // Implementación Shoelace opcional:
        List<Lado> lados = getLados();
        try {
            // Intentar extraer puntos ordenados: puntoA del primer lado + puntoB de cada lado
            double area = 0;
            // Recolectar vértices en orden: asumir lados consecutivos comparten vértices
            // Si no comparten, igualmente se calcula con los puntos disponibles
            java.util.List<Punto> vertices = new java.util.ArrayList<>();
            vertices.add(lados.get(0).getPuntoA());
            for (Lado l : lados) {
                vertices.add(l.getPuntoB());
            }
            int n = vertices.size() - 1; // último duplicado si es cerrado
            // Shoelace
            for (int i = 0; i < n; i++) {
                Punto p1 = vertices.get(i);
                Punto p2 = vertices.get(i + 1);
                area += (p1.getX() * p2.getY() - p2.getX() * p1.getY());
            }
            return Math.abs(area) / 2.0;
        } catch (Exception e) {
            throw new UnsupportedOperationException("Calcular área de cuadrilátero genérico requiere geometría válida", e);
        }
    }
}
