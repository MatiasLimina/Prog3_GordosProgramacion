package Ejercicio_01;

public class Elipse extends Figura {

    protected double radioMayor;
    protected double radioMenor;

    /**
     * Constructor para una Elipse.
     * @param color El color de la figura.
     * @param radioMayor El radio mayor de la elipse.
     * @param radioMenor El radio menor de la elipse.
     */
    public Elipse(String color, double radioMayor, double radioMenor) {
        super(color);
        this.radioMayor = radioMayor;
        this.radioMenor = radioMenor;
    }

    /**
     * Calcula el área de la elipse.
     * @return El área calculada.
     */
    @Override
    public double calcularArea() {
        return Math.PI * radioMayor * radioMenor;
    }

}

