package Ejercicio_01;

public abstract class Figura {

    /**
     * Atributo que representa el color de la figura.
     * Es protected para que las clases hijas puedan acceder a él directamente.
     * No está en el enunciado estricto, se mantiene por compatibilidad.
     * Ver ANALISIS_Ejercicio_01.md §9 duda #5.
     */
    protected String color;

    /**
     * Constructor para inicializar los atributos comunes de una figura.
     * @param color El color de la figura (puede ser null si no aplica).
     */
    public Figura(String color) {
        this.color = color;
    }

    public String getColor() {
        return color;
    }

    public void setColor(String color) {
        this.color = color;
    }

    public abstract double calcularArea();
}
