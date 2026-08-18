package Ejercicio_01;

public class Circulo extends Elipse {

    private double radio;

    /**
     * Constructor para un Círculo.
     * Un círculo es un caso especial de una elipse donde ambos radios son iguales.
     * @param color El color de la figura.
     * @param radio El radio del círculo.
     */
    public Circulo(String color, double radio) {
        // Llama al constructor de la clase padre (Elipse)
        // con el mismo valor para el radio mayor y menor.
        super(color, radio, radio);
        this.radio = radio;
    }

    public double getRadio() {
        return radio;
    }
}

