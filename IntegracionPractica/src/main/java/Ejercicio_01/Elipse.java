package Ejercicio_01;

public class Elipse extends Figura {

    protected double radioMayor;
    protected double radioMenor;

    /**
     * Constructor para una Elipse.
     * @param color El color de la figura.
     * @param radioMayor El radio mayor de la elipse (>0).
     * @param radioMenor El radio menor de la elipse (>0).
     */
    public Elipse(String color, double radioMayor, double radioMenor) {
        super(color);
        if (radioMayor <= 0 || radioMenor <= 0) {
            throw new IllegalArgumentException("Radios deben ser > 0");
        }
        this.radioMayor = radioMayor;
        this.radioMenor = radioMenor;
    }

    public double getRadioMayor() {
        return radioMayor;
    }

    public double getRadioMenor() {
        return radioMenor;
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

