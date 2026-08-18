package Ejercicio_01;

public abstract class Figura {

    /**
     * Atributo que representa el color de la figura.
     * Es protected para que las clases hijas puedan acceder a él directamente.
     */
    protected String color;

    /**
     * Constructor para inicializar los atributos comunes de una figura.
     * @param color El color de la figura.
     */
    public Figura(String color) {
        this.color = color;
    }

    public abstract double calcularArea();
}
